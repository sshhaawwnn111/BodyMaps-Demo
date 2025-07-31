import nibabel as nib
import matplotlib.pyplot as plt
import numpy as np
import os
from matplotlib.colors import ListedColormap

def convert_nii_to_png(nii_path, output_dir, max_slices=5):
    """
    Convert NIfTI file to PNG slices for preview
    
    Args:
        nii_path: Path to the .nii.gz file
        output_dir: Directory to save PNG files
        max_slices: Maximum number of slices to generate
    """
    try:
        # Load the NIfTI file
        img = nib.load(nii_path)
        data = img.get_fdata()
        
        # Get filename without extension
        base_name = os.path.basename(nii_path).replace('.nii.gz', '').replace('.nii', '')
        
        # Handle different data types
        if 'combined' in base_name or 'label' in base_name:
            # This is likely a segmentation mask
            data = data.astype(np.uint8)
            # Get unique labels (excluding background)
            unique_labels = np.unique(data)
            unique_labels = unique_labels[unique_labels > 0]
            
            if len(unique_labels) == 0:
                print(f"No segmentation data found in {nii_path}")
                return
        else:
            # This is likely a single organ segmentation
            # Binarize the data
            data = (data > 0).astype(np.uint8)
        
        # Get the middle slices (axial view)
        if len(data.shape) == 3:
            z_dim = data.shape[2]
            # Select slices around the middle
            start_slice = max(0, z_dim // 2 - max_slices // 2)
            end_slice = min(z_dim, start_slice + max_slices)
            
            slice_indices = range(start_slice, end_slice)
        else:
            print(f"Unexpected data shape: {data.shape}")
            return
        
        # Generate PNG files for selected slices
        for i, slice_idx in enumerate(slice_indices):
            slice_data = data[:, :, slice_idx]
            
            # Skip empty slices
            if np.sum(slice_data) == 0:
                continue
            
            plt.figure(figsize=(8, 8))
            plt.imshow(slice_data, cmap='viridis' if 'combined' in base_name else 'Reds', 
                      interpolation='nearest', origin='lower')
            plt.colorbar(shrink=0.8)
            plt.title(f'{base_name} - Slice {slice_idx}')
            plt.axis('off')
            
            # Save the image
            output_path = os.path.join(output_dir, f'{base_name}_slice_{slice_idx:03d}.png')
            plt.savefig(output_path, bbox_inches='tight', dpi=100, facecolor='white')
            plt.close()
            
        print(f"Generated preview images for {base_name}")
        
    except Exception as e:
        print(f"Error converting {nii_path} to PNG: {str(e)}")

def create_overlay_image(ct_path, seg_path, output_dir, slice_idx=None):
    """
    Create overlay images of CT scan with segmentation
    
    Args:
        ct_path: Path to the CT scan .nii.gz file
        seg_path: Path to the segmentation .nii.gz file
        output_dir: Directory to save overlay images
        slice_idx: Specific slice index, if None will use middle slice
    """
    try:
        # Load both images
        ct_img = nib.load(ct_path)
        seg_img = nib.load(seg_path)
        
        ct_data = ct_img.get_fdata()
        seg_data = seg_img.get_fdata()
        
        # Normalize CT data
        ct_data = np.clip(ct_data, -1000, 1000)  # Typical CT window
        ct_data = (ct_data + 1000) / 2000  # Normalize to 0-1
        
        if slice_idx is None:
            slice_idx = ct_data.shape[2] // 2
        
        ct_slice = ct_data[:, :, slice_idx]
        seg_slice = seg_data[:, :, slice_idx]
        
        # Create overlay
        plt.figure(figsize=(12, 6))
        
        # Original CT
        plt.subplot(1, 2, 1)
        plt.imshow(ct_slice, cmap='gray', origin='lower')
        plt.title('Original CT')
        plt.axis('off')
        
        # CT with segmentation overlay
        plt.subplot(1, 2, 2)
        plt.imshow(ct_slice, cmap='gray', origin='lower')
        
        # Create a masked array for the segmentation
        seg_masked = np.ma.masked_where(seg_slice == 0, seg_slice)
        plt.imshow(seg_masked, cmap='hot', alpha=0.6, origin='lower')
        plt.title('CT with Segmentation Overlay')
        plt.axis('off')
        
        # Save the overlay
        base_name = os.path.basename(seg_path).replace('.nii.gz', '')
        output_path = os.path.join(output_dir, f'{base_name}_overlay_slice_{slice_idx:03d}.png')
        plt.savefig(output_path, bbox_inches='tight', dpi=100, facecolor='white')
        plt.close()
        
        print(f"Generated overlay image: {output_path}")
        
    except Exception as e:
        print(f"Error creating overlay image: {str(e)}")

if __name__ == "__main__":
    # Test function
    import sys
    if len(sys.argv) > 2:
        convert_nii_to_png(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python nii_to_png.py <input.nii.gz> <output_directory>")
