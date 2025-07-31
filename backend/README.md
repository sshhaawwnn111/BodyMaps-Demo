# BodyMaps Backend (Flask)

This is the Flask backend API for the BodyMaps SuPreM Segmentation Demo.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Create required directories
mkdir -p inputs_data outputs_data static/results static/segmentation_preview

# Start the server
python app.py
```

The API will run on http://localhost:5001.

## 📋 Prerequisites

- Python 3.8+
- Docker (for SuPreM model)
- SuPreM Docker image: `docker pull qchen99/suprem:v1`

## 🏗 Modular Architecture

The backend is now organized into separate modules for better maintainability:

- `api/upload.py` - File upload and case management
- `api/processing.py` - Docker processing and monitoring  
- `api/results.py` - Result downloads
- `api/imaging.py` - CT viewing and interactive segmentation
- `config.py` - Configuration management
- `utils/` - Utility functions

See [API_STRUCTURE.md](API_STRUCTURE.md) for detailed documentation.

## 🔗 API Endpoints

All endpoints are prefixed with `/api/`:

### Upload & Case Management
- `POST /api/upload` - Upload .nii.gz files
- `GET /api/list_uploads` - List uploaded cases
- `DELETE /api/delete_upload/<case_name>` - Delete a case

### Processing & Monitoring
- `POST /api/run_docker` - Start SuPreM processing
- `GET /api/status/<case_name>` - Get processing status
- `GET /api/logs/<case_name>` - Get processing logs

### Results & Downloads
- `GET /api/download/<case_name>` - Download results ZIP

### Imaging & Visualization
- `GET /api/original_slice/<case_name>/<slice_idx>` - Get CT slice image
- `GET /api/slice_with_overlay/<case_name>/<slice_idx>` - Get CT slice with segmentation overlay
- `POST /api/interact_segment` - Interactive segmentation
- `GET /api/segmentation_preview/<case_name>/<slice_idx>` - Get segmentation preview

## 🔧 Configuration

The app creates the following directories:
- `inputs_data/` - Uploaded CT scans
- `outputs_data/` - SuPreM segmentation results
- `static/results/` - Generated preview images
- `static/segmentation_preview/` - Interactive segmentation previews