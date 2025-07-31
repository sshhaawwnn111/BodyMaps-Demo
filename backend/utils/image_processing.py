"""
Image processing utilities
Handles NIfTI to PNG conversion and preview generation
"""

import os

def generate_preview_images(case_name):
    """Generate PNG preview images from segmentation results"""
    from app import app
    
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