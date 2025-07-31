"""
Results API endpoints
Handles result downloads and file serving
"""

import os
import shutil
from flask import Blueprint, jsonify, send_file, after_this_request

results_bp = Blueprint('results', __name__)

@results_bp.route('/download/<case_name>')
def download_results(case_name):
    """Download results as zip file"""
    from app import app
    
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