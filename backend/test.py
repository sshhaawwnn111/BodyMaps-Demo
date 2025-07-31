import os
import torch
import SimpleITK as sitk
import matplotlib.pyplot as plt
import numpy as np

os.environ["nnUNet_raw"] = "/home/sshha/projects/BodyMaps-Demo/nnUNet_raw"
os.environ["nnUNet_preprocessed"] = "/home/sshha/projects/BodyMaps-Demo/nnUNet_preprocessed"
os.environ["nnUNet_results"] = "/home/sshha/projects/BodyMaps-Demo/nnUNet_results"

# --- Initialize Inference Session ---
from nnInteractive.inference.inference_session import nnInteractiveInferenceSession

# --- Download Trained Model Weights (~400MB) ---
REPO_ID = "nnInteractive/nnInteractive"
MODEL_NAME = "nnInteractive_v1.0"  # Updated models may be available in the future
DOWNLOAD_DIR = os.path.join(os.getcwd(), "models")  # Download to ./models
POINT_COORDINATES = (350, 174, 35)    # Example: (x, y, z) for a positive point
TEST_IMAGE = "inputs_data/casename00001/ct.nii.gz"          # Path to your test image

session = nnInteractiveInferenceSession(
    device=torch.device("cuda:0"),  # Set inference device
    use_torch_compile=False,  # Experimental: Not tested yet
    verbose=False,
    torch_n_threads=os.cpu_count(),  # Use available CPU cores
    do_autozoom=True,  # Enables AutoZoom for better patching
    use_pinned_memory=True,  # Optimizes GPU memory transfers
)

# Load the trained model
model_path = os.path.join(DOWNLOAD_DIR, MODEL_NAME)
session.initialize_from_trained_model_folder(model_path)

# --- Load Input Image (Example with SimpleITK) ---
input_image = sitk.ReadImage(TEST_IMAGE)
img = sitk.GetArrayFromImage(input_image)  # (z, y, x)
img = np.transpose(img, (2, 1, 0))        # (x, y, z)
img = img[None]                           # (1, x, y, z)

print(f"Input image shape: {img.shape}")
# Validate input dimensions
if img.ndim != 4:
    raise ValueError("Input image must be 4D with shape (1, x, y, z)")

session.set_image(img)

# Add this after session.set_image(img) to see what happened to your image
print(f"Original image shape: {img.shape}")
print(f"Session image shape: {session.current_image.shape if hasattr(session, 'current_image') else 'Not available'}")

# Also check the interaction map bounds
print(f"Interaction map shape: {session.interaction_map.shape if hasattr(session, 'interaction_map') else 'Not available'}")

# --- Define Output Buffer ---
target_tensor = torch.zeros(img.shape[1:], dtype=torch.uint8)  # Must be 3D (x, y, z)
session.set_target_buffer(target_tensor)

# --- Interacting with the Model ---
# Interactions can be freely chained and mixed in any order. Each interaction refines the segmentation.
# The model updates the segmentation mask in the target buffer after every interaction.

# Example: Add a **positive** point interaction
# POINT_COORDINATES should be a tuple (x, y, z) specifying the point location.
session.add_point_interaction(POINT_COORDINATES, include_interaction=True)

print("point interaction added at:", POINT_COORDINATES)

# --- Retrieve and Save Result ---
result = session.target_buffer.cpu().numpy()
result = np.transpose(result, (2, 1, 0))  # (z, y, x)
result_img = sitk.GetImageFromArray(result)
result_img.CopyInformation(input_image)
sitk.WriteImage(result_img, "segmentation_result.nii.gz")

print("Segmentation complete. Result saved as segmentation_result.nii.gz")

# --- Visualization ---
# Show the middle slice in z-dimension
input_np = sitk.GetArrayFromImage(input_image)  # shape: (z, y, x)
seg_np = result  # shape: (z, y, x)

point_slice = POINT_COORDINATES[2]

plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.title(f"Input Image (slice {point_slice})")
plt.imshow(input_np[point_slice], cmap='gray')
plt.scatter(POINT_COORDINATES[0], POINT_COORDINATES[1], c='red', s=80, marker='x', label='Point')
plt.legend()
plt.axis('off')

plt.subplot(1, 2, 2)
plt.title(f"Segmentation (slice {point_slice})")
plt.imshow(input_np[point_slice], cmap='gray')
plt.imshow(seg_np[point_slice], alpha=0.5, cmap='jet')
plt.scatter(POINT_COORDINATES[0], POINT_COORDINATES[1], c='red', s=80, marker='x', label='Point')
plt.legend()
plt.axis('off')

plt.tight_layout()
plt.savefig("segmentation_visualization.png")
print("Visualization saved as segmentation_visualization.png")
print("Unique values in segmentation:", np.unique(seg_np[point_slice]))