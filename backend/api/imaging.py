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
        
        session = nnInteractiveInferenceSession(
            device=torch.device("cuda:0" if torch.cuda.is_available() else "cpu"),
            use_torch_compile=False,
            verbose=False,
            torch_n_threads=os.cpu_count(),
            do_autozoom=True,
            use_pinned_memory=True,
        )
        session.initialize_from_trained_model_folder(model_dir)
        
        # Load image
        input_image = sitk.ReadImage(case_path)
        img = sitk.GetArrayFromImage(input_image)  # (z, y, x)
        img = np.transpose(img, (2, 1, 0))        # (x, y, z)
        img = img[None]                           # (1, x, y, z)
        session.set_image(img)
        
        # Set target buffer
        target_tensor = torch.zeros(img.shape[1:], dtype=torch.uint8)
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
    """Get CT slice with current segmentation overlay"""
    from app import app
    
    try:
        print(f"DEBUG: slice_with_overlay called for {case_name}, slice {slice_idx}")
        
        # Get original slice
        ct_path = os.path.join(app.config['UPLOAD_FOLDER'], case_name, 'ct.nii.gz')
        if not os.path.exists(ct_path):
            print(f"DEBUG: CT file not found: {ct_path}")
            return jsonify({'error': 'Original CT not found'}), 404
            
        if nib is None:
            print("DEBUG: nibabel not available")
            return jsonify({'error': 'nibabel not installed on server'}), 500
            
        print("DEBUG: Loading image with nibabel")
        img = nib.load(ct_path)
        data = img.get_fdata()
        print(f"DEBUG: Image loaded, shape: {data.shape}")
        
        # Validate slice index
        if slice_idx < 0 or slice_idx >= data.shape[2]:
            slice_idx = data.shape[2] // 2
            print(f"DEBUG: Adjusted slice index to: {slice_idx}")
            
        slice_img = data[:, :, slice_idx]
        print(f"DEBUG: Extracted slice, shape: {slice_img.shape}")
        
        # Check if we have an active session with segmentation
        overlay_mask = None
        interaction_points = []
        
        print("DEBUG: Checking for active sessions")
        try:
            with nn_sessions_lock:
                if case_name in nn_sessions and INTERACTIVE_AVAILABLE:
                    print("DEBUG: Found active session, getting segmentation")
                    session = nn_sessions[case_name]
                    # Get segmentation for this slice
                    seg_np = session.target_buffer.cpu().numpy()  # (x, y, z)
                    seg_np = np.transpose(seg_np, (2, 1, 0))     # (z, y, x)
                    if slice_idx < seg_np.shape[0]:
                        overlay_mask = seg_np[slice_idx]  # (y, x)
                        print(f"DEBUG: Got overlay mask, shape: {overlay_mask.shape}")
                    
                    # Get interaction points for this slice
                    interaction_points = [
                        {'x': p[0], 'y': p[1], 'positive': p[3]} 
                        for p in getattr(session, 'interaction_points', []) 
                        if p[2] == slice_idx
                    ]
                    print(f"DEBUG: Got {len(interaction_points)} interaction points")
                else:
                    print("DEBUG: No active session found")
        except Exception as e:
            print(f"DEBUG: Error getting segmentation overlay: {e}")
            # Continue without overlay
            interaction_points = []
        
        print("DEBUG: Normalizing image")
        # Normalize image to 0-255
        slice_img = np.nan_to_num(slice_img)
        vmin, vmax = np.percentile(slice_img, [1, 99])
        slice_img = np.clip((slice_img - vmin) / (vmax - vmin + 1e-5), 0, 1)
        
        # Create RGB image
        img_rgb = np.stack([slice_img] * 3, axis=-1)
        print(f"DEBUG: Created RGB image, shape: {img_rgb.shape}")
        
        # Apply overlay if available
        if overlay_mask is not None:
            print("DEBUG: Applying segmentation overlay")
            print(f"DEBUG: slice_img shape: {slice_img.shape}, overlay_mask shape: {overlay_mask.shape}")
            
            # Ensure overlay mask matches slice dimensions
            if overlay_mask.shape != slice_img.shape:
                print(f"DEBUG: Reshaping overlay mask from {overlay_mask.shape} to {slice_img.shape}")
                # The segmentation might be transposed relative to the image
                if overlay_mask.shape == (slice_img.shape[1], slice_img.shape[0]):
                    overlay_mask = overlay_mask.T
                else:
                    print("DEBUG: Cannot match overlay dimensions, skipping overlay")
                    overlay_mask = None
            
            if overlay_mask is not None:
                mask = overlay_mask > 0
                img_rgb[mask, 0] = np.clip(img_rgb[mask, 0] + 0.3, 0, 1)  # Add red
                img_rgb[mask, 1] = np.clip(img_rgb[mask, 1] * 0.7, 0, 1)  # Reduce green
                img_rgb[mask, 2] = np.clip(img_rgb[mask, 2] * 0.7, 0, 1)  # Reduce blue
        
        # Convert to 8-bit
        img_rgb = (img_rgb * 255).astype(np.uint8)
        print("DEBUG: Converted to 8-bit")
        
        # Create PIL image
        print("DEBUG: Creating PIL image")
        im = Image.fromarray(img_rgb)
        buf = BytesIO()
        im.save(buf, format='PNG')
        buf.seek(0)
        print(f"DEBUG: Created PNG, size: {len(buf.getvalue())} bytes")
        
        return send_file(buf, mimetype='image/png')
        
    except Exception as e:
        print(f"DEBUG: Exception in slice_with_overlay: {e}")
        import traceback
        traceback.print_exc()
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
    
    try:
        session = get_nn_session(case_name)
        
        # Add interaction point
        session.add_point_interaction((x, y, z), include_interaction=positive)
        
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