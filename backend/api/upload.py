"""
Upload API endpoints
Handles file upload functionality
"""

import os
import glob
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

upload_bp = Blueprint('upload', __name__)

def get_next_case_name(upload_folder):
    """Generate the next case name (casename00001, casename00002, etc.)"""
    existing_cases = glob.glob(os.path.join(upload_folder, 'casename*'))
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

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    from app import app, processing_status
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Please upload a .nii.gz file'}), 400
    
    try:
        # Generate case name and create directory
        case_name = get_next_case_name(app.config['UPLOAD_FOLDER'])
        case_dir = os.path.join(app.config['UPLOAD_FOLDER'], case_name)
        os.makedirs(case_dir, exist_ok=True)
        
        # Save the uploaded file as ct.nii.gz
        file_path = os.path.join(case_dir, 'ct.nii.gz')
        file.save(file_path)
        
        # Initialize processing status
        processing_status[case_name] = {'status': 'uploaded', 'message': 'File uploaded successfully'}
        
        return jsonify({
            'success': True, 
            'case_name': case_name,
            'message': f'File uploaded as {case_name}. Ready for processing.'
        })
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@upload_bp.route('/list_uploads')
def list_uploads():
    """List all uploaded files/cases in inputs_data"""
    from app import app
    
    uploads = []
    base_dir = app.config['UPLOAD_FOLDER']
    if os.path.exists(base_dir):
        for case_name in sorted(os.listdir(base_dir)):
            case_path = os.path.join(base_dir, case_name)
            if os.path.isdir(case_path):
                files = [f for f in os.listdir(case_path) if os.path.isfile(os.path.join(case_path, f))]
                uploads.append({'case_name': case_name, 'files': files})
    return jsonify({'uploads': uploads})

@upload_bp.route('/delete_upload/<case_name>', methods=['DELETE'])
def delete_upload(case_name):
    """Delete an uploaded case and its files"""
    from app import app, processing_status
    import shutil
    
    base_dir = app.config['UPLOAD_FOLDER']
    case_dir = os.path.join(base_dir, case_name)
    if not os.path.exists(case_dir):
        return jsonify({'error': 'Case not found'}), 404
    try:
        shutil.rmtree(case_dir)
        # Remove from processing_status if present
        processing_status.pop(case_name, None)
        return jsonify({'success': True, 'message': f'{case_name} deleted.'})
    except Exception as e:
        return jsonify({'error': f'Failed to delete: {str(e)}'}), 500