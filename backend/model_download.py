import os
import torch
import SimpleITK as sitk
from huggingface_hub import snapshot_download  # Install huggingface_hub if not already installed

# --- Download Trained Model Weights (~400MB) ---
REPO_ID = "nnInteractive/nnInteractive"
MODEL_NAME = "nnInteractive_v1.0"  # Updated models may be available in the future
DOWNLOAD_DIR = os.path.join(os.getcwd(), "models")  # Download to ./models

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

download_path = snapshot_download(
    repo_id=REPO_ID,
    allow_patterns=[f"{MODEL_NAME}/*"],
    local_dir=DOWNLOAD_DIR
)

print(f"All models downloaded to: {download_path}")