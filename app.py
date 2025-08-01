import os
import shutil
import subprocess
import threading
from flask import Flask, request, render_template, jsonify, send_file, redirect, url_for, after_this_request
from werkzeug.utils import secure_filename
import time
import glob

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = 'inputs_data'
app.config['OUTPUT_FOLDER'] = 'outputs_data'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs('static/results', exist_ok=True)

# Track processing status
processing_status = {}

def get_next_case_name():
    """Generate the next case name (casename00001, casename00002, etc.)"""
    existing_cases = glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], 'casename*'))
    if not existing_cases:
        return 'casename00001'
    
    # Extract numbers and find the highest
    case_numbers = []
    for case_path in existing_cases:
        case_name = os.path.basename(case_path)
        if case_name.startswith('casename') and len(case_name) == 13:  # casename + 5 digits
            try:
                number = int(case_name[8:])  # Extract the 5-digit number
                case_numbers.append(number)
            except ValueError:
                continue
    
    if case_numbers:
        next_number = max(case_numbers) + 1
    else:
        next_number = 1
    
    return f'casename{next_number:05d}'

def allowed_file(filename):
    """Check if uploaded file is a valid .nii.gz file"""
    return '.' in filename and filename.lower().endswith('.nii.gz')

def run_suprem_docker(case_name):
    """Run SuPreM Docker container for segmentation"""
    container_id = None
    try:
        processing_status[case_name] = {'status': 'running', 'message': 'Starting SuPreM segmentation...', 'logs': []}
        
        # Check if running on Apple Silicon Mac
        import platform
        is_apple_silicon = platform.machine() == 'arm64'
        
        # Base Docker command
        docker_cmd = ['docker', 'container', 'run']
        
        # Add platform specification for Apple Silicon
        if is_apple_silicon:
            docker_cmd.extend(['--platform', 'linux/amd64'])
        
        # Add memory limit (reduce for Apple Silicon)
        memory_limit = '64G' if is_apple_silicon else '128G'
        docker_cmd.extend(['-m', memory_limit])
        
        # Add GPU support only if not on Apple Silicon
        if not is_apple_silicon:
            try:
                # Test if nvidia-docker is available
                subprocess.run(['nvidia-smi'], capture_output=True, check=True)
                docker_cmd.extend(['--gpus', 'device=0'])
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("Warning: GPU not available, running on CPU")
        else:
            print("Running on Apple Silicon - CPU mode only")
        
        # Add remaining arguments
        docker_cmd.extend([
            '--rm',
            '-v', f'{os.path.abspath(app.config["UPLOAD_FOLDER"])}:/workspace/inputs/',
            '-v', f'{os.path.abspath(app.config["OUTPUT_FOLDER"])}:/workspace/outputs/',
            'qchen99/suprem:v1',
            '/bin/bash', '-c', 'sh predict.sh'
        ])
        print(f"Running Docker command: {' '.join(docker_cmd)}")
        processing_status[case_name]['logs'].append(f"Command: {' '.join(docker_cmd)}")
        
        # Start the Docker process
        process = subprocess.Popen(docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
        
        # Get container ID for monitoring
        time.sleep(2)  # Wait for container to start
        try:
            container_result = subprocess.run(['docker', 'ps', '--latest', '--quiet'], capture_output=True, text=True)
            if container_result.returncode == 0 and container_result.stdout.strip():
                container_id = container_result.stdout.strip()
                processing_status[case_name]['container_id'] = container_id
                processing_status[case_name]['logs'].append(f"Container started: {container_id}")
        except Exception as e:
            print(f"Could not get container ID: {e}")
        
        # Read output in real-time
        timeout = 7200 if is_apple_silicon else 3600  # 2 hours for Apple Silicon, 1 hour for others
        start_time = time.time()
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                log_line = output.strip()
                print(f"Docker output: {log_line}")
                
                # Store logs in processing status (keep last 50 lines)
                if 'logs' not in processing_status[case_name]:
                    processing_status[case_name]['logs'] = []
                processing_status[case_name]['logs'].append(log_line)
                if len(processing_status[case_name]['logs']) > 50:
                    processing_status[case_name]['logs'] = processing_status[case_name]['logs'][-50:]
                
                # Update status message based on logs
                if 'test len' in log_line:
                    processing_status[case_name]['message'] = 'Loading data and initializing model...'
                elif 'Loading' in log_line or 'loading' in log_line:
                    processing_status[case_name]['message'] = f'Loading: {log_line}'
                elif 'Processing' in log_line or 'processing' in log_line:
                    processing_status[case_name]['message'] = f'Processing: {log_line}'
                elif 'Segmenting' in log_line or 'segmenting' in log_line:
                    processing_status[case_name]['message'] = f'Segmenting: {log_line}'
                elif 'Saving' in log_line or 'saving' in log_line:
                    processing_status[case_name]['message'] = f'Saving results: {log_line}'
            
            # Check timeout
            if time.time() - start_time > timeout:
                process.terminate()
                raise subprocess.TimeoutExpired(docker_cmd, timeout)
        
        # Wait for process to complete
        return_code = process.wait()
        
        if return_code == 0:
            processing_status[case_name] = {
                'status': 'completed', 
                'message': 'Segmentation completed successfully!',
                'output_path': os.path.join(app.config['OUTPUT_FOLDER'], case_name),
                'logs': processing_status[case_name].get('logs', [])
            }
            
            # Generate preview images
            generate_preview_images(case_name)
            
        else:
            processing_status[case_name] = {
                'status': 'error', 
                'message': f'Docker execution failed with return code: {return_code}',
                'logs': processing_status[case_name].get('logs', [])
            }
            
    except subprocess.TimeoutExpired:
        processing_status[case_name] = {
            'status': 'error', 
            'message': f'Processing timed out after {timeout//60} minutes',
            'logs': processing_status[case_name].get('logs', [])
        }
        if container_id:
            try:
                subprocess.run(['docker', 'stop', container_id], capture_output=True)
            except:
                pass
    except Exception as e:
        processing_status[case_name] = {
            'status': 'error', 
            'message': f'Error during processing: {str(e)}',
            'logs': processing_status[case_name].get('logs', [])
        }

def generate_preview_images(case_name):
    """Generate PNG preview images from segmentation results"""
    try:
        from utils.nii_to_png import convert_nii_to_png
        
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], case_name, 'segmentations')
        preview_dir = os.path.join('static', 'results', case_name)
        os.makedirs(preview_dir, exist_ok=True)
        
        # Convert key segmentation files to PNG
        key_files = ['liver.nii.gz', 'kidney_left.nii.gz', 'kidney_right.nii.gz', 'combined_labels.nii.gz']
        
        for nii_file in key_files:
            nii_path = os.path.join(output_dir, nii_file)
            if os.path.exists(nii_path):
                convert_nii_to_png(nii_path, preview_dir, max_slices=5)
                
    except Exception as e:
        print(f"Error generating preview images: {str(e)}")

@app.route('/')
def index():
    """Main upload page"""
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Please upload a .nii.gz file'}), 400
    
    try:
        # Generate case name and create directory
        case_name = get_next_case_name()
        case_dir = os.path.join(app.config['UPLOAD_FOLDER'], case_name)
        os.makedirs(case_dir, exist_ok=True)
        
        # Save the uploaded file as ct.nii.gz
        file_path = os.path.join(case_dir, 'ct.nii.gz')
        file.save(file_path)
        
        # Initialize processing status
        processing_status[case_name] = {'status': 'uploaded', 'message': 'File uploaded successfully'}
        
        # Start SuPreM processing in background
        thread = threading.Thread(target=run_suprem_docker, args=(case_name,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True, 
            'case_name': case_name,
            'message': f'File uploaded as {case_name}. Processing started...'
        })
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/status/<case_name>')
def get_status(case_name):
    """Get processing status for a case"""
    status = processing_status.get(case_name, {'status': 'unknown', 'message': 'Case not found'})
    return jsonify(status)

@app.route('/logs/<case_name>')
def get_logs(case_name):
    """Get detailed logs for a case"""
    status = processing_status.get(case_name, {})
    logs = status.get('logs', [])
    container_id = status.get('container_id', None)
    
    # Try to get fresh logs from Docker if container is running
    if container_id:
        try:
            result = subprocess.run(['docker', 'logs', '--tail', '20', container_id], 
                                 capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                fresh_logs = result.stdout.strip().split('\n')
                # Combine stored logs with fresh Docker logs
                all_logs = logs + ['--- Fresh Docker Logs ---'] + fresh_logs
                return jsonify({'logs': all_logs[-50:]})  # Return last 50 lines
        except:
            pass
    
    return jsonify({'logs': logs})

@app.route('/results/<case_name>')
def view_results(case_name):
    """View results page for a case"""
    status = processing_status.get(case_name, {})
    if status.get('status') != 'completed':
        return redirect(url_for('index'))
    
    # Get available preview images
    preview_dir = os.path.join('static', 'results', case_name)
    images = []
    if os.path.exists(preview_dir):
        for img_file in sorted(os.listdir(preview_dir)):
            if img_file.endswith('.png'):
                images.append(f'results/{case_name}/{img_file}')
    
    return render_template('results.html', case_name=case_name, images=images)

@app.route('/download/<case_name>')
def download_results(case_name):
    """Download results as zip file"""
    try:
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], case_name)
        if not os.path.exists(output_dir):
            return jsonify({'error': 'Results not found'}), 404
        
        # Create zip file
        zip_path = f'/tmp/{case_name}_results.zip'
        shutil.make_archive(zip_path.replace('.zip', ''), 'zip', output_dir)
        
        @after_this_request
        def remove_file(response):
            try:
                os.remove(zip_path)
            except Exception as e:
                print(f"Error deleting zip file: {e}")
            return response

        return send_file(zip_path, as_attachment=True, download_name=f'{case_name}_results.zip')
        
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
