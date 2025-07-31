"""
Imaging API endpoints
Handles CT slice viewing and interactive segmentation
"""

import os
import numpy as np
from io import BytesIO
from flask import Blueprint, request, jsonify, send_file
from PIL import Image

try:
    import nibabel as nib
except ImportError:
    nib = None

try:
    import torch
    import SimpleITK as sitk
    from threading import Lock
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    
    # --- nnInteractive session cache ---
    nn_sessions = {}
    nn_sessions_lock = Lock()
    INTERACTIVE_AVAILABLE = True
    
    # Set nnUNet environment variables
    import os
    if not os.environ.get("nnUNet_raw"):
        os.environ["nnUNet_raw"] = os.path.join(os.getcwd(), "nnUNet_raw")
    if not os.environ.get("nnUNet_preprocessed"):
        os.environ["nnUNet_preprocessed"] = os.path.join(os.getcwd(), "nnUNet_preprocessed")
    if not os.environ.get("nnUNet_results"):
        os.environ["nnUNet_results"] = os.path.join(os.getcwd(), "nnUNet_results")
        
except ImportError:
    INTERACTIVE_AVAILABLE = False
    print("Warning: Interactive segmentation dependencies not available")

imaging_bp = Blueprint('imaging', __name__)

@imaging_bp.route('/original_slice/<case_name>/<int:slice_idx>')
def get_original_slice(case_name, slice_idx):
    """Serve a PNG of the requested slice from the original ct.nii.gz for a case."""
    from app import app
    
    ct_path = os.path.join(app.config['UPLOAD_FOLDER'], case_name, 'ct.nii.gz')
    if not os.path.exists(ct_path):
        return jsonify({'error': 'Original CT not found'}), 404
    if nib is None:
        return jsonify({'error': 'nibabel not installed on server'}), 500
    try:
        img = nib.load(ct_path)
        data = img.get_fdata()
        # Use axial slices (assume shape: (H, W, Slices)), get middle if out of bounds
        if slice_idx < 0 or slice_idx >= data.shape[2]:
            slice_idx = data.shape[2] // 2
        slice_img = data[:, :, slice_idx]
        # Normalize to 0-255 for PNG
        slice_img = np.nan_to_num(slice_img)
        vmin, vmax = np.percentile(slice_img, [1, 99])
        slice_img = np.clip((slice_img - vmin) / (vmax - vmin + 1e-5), 0, 1)
        slice_img = (slice_img * 255).astype(np.uint8)
        im = Image.fromarray(slice_img)
        buf = BytesIO()
        im.save(buf, format='PNG')
        buf.seek(0)
        return send_file(buf, mimetype='image/png')
    except Exception as e:
        return jsonify({'error': f'Failed to extract slice: {str(e)}'}), 500

def get_nn_session(case_name):
    """Get or create a nnInteractiveInferenceSession for a case."""
    if not INTERACTIVE_AVAILABLE:
        raise ImportError("Interactive segmentation dependencies not available")
        
    from nnInteractive.inference.inference_session import nnInteractiveInferenceSession
    from app import app
    
    model_dir = os.path.join(os.getcwd(), "models", "nnInteractive_v1.0")
    case_path = os.path.join(app.config['UPLOAD_FOLDER'], case_name, 'ct.nii.gz')
    if not os.path.exists(case_path):
        raise FileNotFoundError(f"No CT found for {case_name}")
    
    with nn_sessions_lock:
        if case_name in nn_sessions:
            return nn_sessions[case_name]
        
        # Match test.py configuration exactly for best results
        session = nnInteractiveInferenceSession(
            device=torch.device("cuda:0" if torch.cuda.is_available() else "cpu"),
            use_torch_compile=False,  # Experimental: Not tested yet
            verbose=False,
            torch_n_threads=os.cpu_count(),  # Use available CPU cores
            do_autozoom=True,  # Enables AutoZoom for better patching - IMPORTANT for quality
            use_pinned_memory=True,  # Optimizes GPU memory transfers
        )
        session.initialize_from_trained_model_folder(model_dir)
        
        # Load image
        input_image = sitk.ReadImage(case_path)
        img = sitk.GetArrayFromImage(input_image)  # (z, y, x)
        img = np.transpose(img, (2, 1, 0))        # (x, y, z)
        img = img[None]                           # (1, x, y, z)
        session.set_image(img)
        
        # Set target buffer - must be 3D (x, y, z) with uint8 dtype (matching test.py)
        target_tensor = torch.zeros(img.shape[1:], dtype=torch.uint8)  # Must be 3D (x, y, z)
        session.set_target_buffer(target_tensor)
        
        # Store additional info
        session.original_image = input_image
        session.interaction_points = []  # Track interaction points
        
        nn_sessions[case_name] = session
        return session

def get_image_info(case_name):
    """Get basic image information (dimensions, etc.)"""
    from app import app
    
    case_path = os.path.join(app.config['UPLOAD_FOLDER'], case_name, 'ct.nii.gz')
    if not os.path.exists(case_path):
        raise FileNotFoundError(f"No CT found for {case_name}")
    
    if nib:
        img = nib.load(case_path)
        data = img.get_fdata()
        spacing = img.header.get_zooms()
        return {
            'shape': list(data.shape),  # Convert to list for JSON serialization
            'max_slice': int(data.shape[2] - 1),  # Convert to int
            'spacing': [float(s) for s in spacing]  # Convert numpy floats to Python floats
        }
    else:
        # Fallback using SimpleITK
        input_image = sitk.ReadImage(case_path)
        img_array = sitk.GetArrayFromImage(input_image)  # (z, y, x)
        spacing = input_image.GetSpacing()
        return {
            'shape': [int(img_array.shape[2]), int(img_array.shape[1]), int(img_array.shape[0])],  # Convert to (x, y, z)
            'max_slice': int(img_array.shape[0] - 1),  # z dimension
            'spacing': [float(s) for s in spacing]  # Convert to Python floats
        }

@imaging_bp.route('/image_info/<case_name>')
def get_case_image_info(case_name):
    """Get image information for a case"""
    try:
        info = get_image_info(case_name)
        return jsonify({'success': True, 'info': info})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404

@imaging_bp.route('/slice_with_overlay/<case_name>/<int:slice_idx>')
def get_slice_with_overlay(case_name, slice_idx):
    """Get CT slice with current segmentation overlay - simplified like test.py"""
    from app import app
    
    try:
        # Load input image (same as test.py)
        ct_path = os.path.join(app.config['UPLOAD_FOLDER'], case_name, 'ct.nii.gz')
        if not os.path.exists(ct_path):
            return jsonify({'error': 'Original CT not found'}), 404
            
        if not INTERACTIVE_AVAILABLE:
            # Fallback to original slice if no interactive segmentation
            return get_original_slice(case_name, slice_idx)
        
        # Load image using SimpleITK (same as test.py)
        input_image = sitk.ReadImage(ct_path)
        input_np = sitk.GetArrayFromImage(input_image)  # shape: (z, y, x)
        
        # Validate slice index
        if slice_idx < 0 or slice_idx >= input_np.shape[0]:
            slice_idx = input_np.shape[0] // 2
        
        # Get segmentation data if session exists
        seg_np = None
        interaction_points = []
        
        with nn_sessions_lock:
            if case_name in nn_sessions:
                session = nn_sessions[case_name]
                # Get segmentation result (same as test.py)
                result = session.target_buffer.cpu().numpy()  # (x, y, z)
                seg_np = np.transpose(result, (2, 1, 0))  # (z, y, x) - same as test.py
                
                # Get interaction points for this slice
                interaction_points = [
                    p for p in getattr(session, 'interaction_points', []) 
                    if p[2] == slice_idx
                ]
        
        # Create visualization with exact pixel dimensions to match frontend
        slice_data = input_np[slice_idx]  # (y, x) = (348, 502)
        height, width = slice_data.shape
        
        # Create figure with exact pixel dimensions (DPI=100 means figsize in inches = pixels/100)
        plt.figure(figsize=(width/100, height/100), dpi=100)
        plt.imshow(slice_data, cmap='gray')
        
        # Debug: Print image and figure info
        print(f"DEBUG: slice_with_overlay - input_np[{slice_idx}] shape: {input_np[slice_idx].shape}")
        print(f"DEBUG: slice_with_overlay - figure size: {width/100:.2f}x{height/100:.2f} inches at 100 DPI = {width}x{height} pixels")
        print(f"DEBUG: slice_with_overlay - interaction_points: {interaction_points}")
        
        # Add segmentation overlay if available (same as test.py)
        if seg_np is not None and seg_np.max() > 0:
            plt.imshow(seg_np[slice_idx], alpha=0.5, cmap='jet')
        
        # Add interaction points (same as test.py)
        for point in interaction_points:
            x, y, z, positive = point
            color = 'red' if positive else 'blue'
            print(f"DEBUG: Drawing point at ({x}, {y}) with color {color}")
            plt.scatter(x, y, c=color, s=80, marker='x', label='Point')
        
        plt.axis('off')
        plt.tight_layout()
        
        # Save to buffer
        buf = BytesIO()
        plt.savefig(buf, format='PNG', bbox_inches='tight', pad_inches=0, dpi=100)
        plt.close()
        buf.seek(0)
        
        return send_file(buf, mimetype='image/png')
        
    except Exception as e:
        print(f"Error in slice_with_overlay: {e}")
        return jsonify({'error': f'Failed to get slice: {str(e)}'}), 500


@imaging_bp.route('/interact_segment', methods=['POST'])
def interact_segment():
    """Handle click and segment"""
    if not INTERACTIVE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Interactive segmentation not available'}), 500
        
    data = request.get_json()
    case_name = data.get('case_name')
    x = int(data.get('x'))
    y = int(data.get('y'))
    z = int(data.get('z'))
    positive = data.get('positive', True)  # True for positive, False for negative
    
    print(f"DEBUG: Received click at ({x}, {y}, {z}) for case {case_name}")
    
    try:
        session = get_nn_session(case_name)
        
        # Debug: Check image dimensions
        if hasattr(session, 'original_image'):
            img_array = sitk.GetArrayFromImage(session.original_image)  # (z, y, x)
            print(f"DEBUG: Original image shape (z,y,x): {img_array.shape}")
            print(f"DEBUG: Click coordinates relative to slice {z}: ({x}, {y})")
            print(f"DEBUG: Max coordinates for this slice: x_max={img_array.shape[2]-1}, y_max={img_array.shape[1]-1}")
        
        # Add interaction point
        # Always use include_interaction=True for smoother segmentation (like test.py)
        # For negative points, we might need to use add_negative_point_interaction if available
        try:
            if positive:
                session.add_point_interaction((x, y, z), include_interaction=True)
            else:
                session.add_point_interaction((x, y, z), include_interaction=False)
        except Exception as e:
            print(f"DEBUG: Error adding interaction point: {e}")
            # Fallback to basic interaction
            session.add_point_interaction((x, y, z), include_interaction=True)
        
        # Store interaction point for visualization
        if not hasattr(session, 'interaction_points'):
            session.interaction_points = []
        session.interaction_points.append((x, y, z, positive))
        
        # Get segmentation statistics
        seg_np = session.target_buffer.cpu().numpy()
        unique_values = np.unique(seg_np)
        
        return jsonify({
            'success': True, 
            'point': {'x': x, 'y': y, 'z': z, 'positive': positive},
            'segmentation_stats': {
                'unique_values': unique_values.tolist(),
                'total_voxels': int(np.sum(seg_np > 0))
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@imaging_bp.route('/clear_segmentation/<case_name>', methods=['POST'])
def clear_segmentation(case_name):
    """Clear all segmentation and interaction points"""
    try:
        with nn_sessions_lock:
            if case_name in nn_sessions:
                session = nn_sessions[case_name]
                # Reset target buffer
                session.target_buffer.zero_()
                # Clear interaction points
                session.interaction_points = []
                return jsonify({'success': True, 'message': 'Segmentation cleared'})
            else:
                return jsonify({'success': False, 'error': 'No active session found'}), 404
                
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@imaging_bp.route('/get_interaction_points/<case_name>/<int:slice_idx>')
def get_interaction_points(case_name, slice_idx):
    """Get interaction points for a specific slice"""
    try:
        with nn_sessions_lock:
            if case_name in nn_sessions:
                session = nn_sessions[case_name]
                points = [
                    {'x': p[0], 'y': p[1], 'positive': p[3]} 
                    for p in getattr(session, 'interaction_points', []) 
                    if p[2] == slice_idx
                ]
                return jsonify({'success': True, 'points': points})
            else:
                return jsonify({'success': True, 'points': []})
                
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@imaging_bp.route('/segmentation_preview/<case_name>/<int:slice_idx>')
def segmentation_preview(case_name, slice_idx):
    """Serve segmentation preview image"""
    img_path = os.path.join('static', 'segmentation_preview', case_name, f'slice_{slice_idx:03d}.png')
    if not os.path.exists(img_path):
        return '', 404
    return send_file(img_path, mimetype='image/png')