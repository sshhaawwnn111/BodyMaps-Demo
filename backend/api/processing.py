"""
Processing API endpoints
Handles Docker processing, status monitoring, and logs
"""

import os
import subprocess
import threading
import time
from flask import Blueprint, request, jsonify

processing_bp = Blueprint('processing', __name__)

def run_suprem_docker(case_name):
    """Run SuPreM Docker container for segmentation"""
    from app import app, processing_status
    from utils.image_processing import generate_preview_images
    
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

@processing_bp.route('/run_docker', methods=['POST'])
def run_docker():
    """Trigger SuPreM Docker processing for a given case_name"""
    from app import app, processing_status
    
    data = request.get_json()
    if not data or 'case_name' not in data:
        return jsonify({'error': 'Missing case_name'}), 400
    case_name = data['case_name']
    # Check if case exists
    case_dir = os.path.join(app.config['UPLOAD_FOLDER'], case_name)
    if not os.path.exists(case_dir):
        return jsonify({'error': 'Case not found'}), 404
    # Prevent duplicate processing
    if processing_status.get(case_name, {}).get('status') in ['running', 'completed']:
        return jsonify({'error': 'Processing already started or completed for this case'}), 400
    # Start SuPreM processing in background
    processing_status[case_name] = {'status': 'processing', 'message': 'Processing started...'}
    thread = threading.Thread(target=run_suprem_docker, args=(case_name,))
    thread.daemon = True
    thread.start()
    return jsonify({'success': True, 'message': f'Processing started for {case_name}.'})

@processing_bp.route('/status/<case_name>')
def get_status(case_name):
    """Get processing status for a case"""
    from app import processing_status
    
    status = processing_status.get(case_name, {'status': 'unknown', 'message': 'Case not found'})
    return jsonify(status)

@processing_bp.route('/logs/<case_name>')
def get_logs(case_name):
    """Get detailed logs for a case"""
    from app import processing_status
    
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