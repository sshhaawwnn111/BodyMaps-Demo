# BodyMaps SuPreM Segmentation Demo

A web-based application for AI-powered medical image segmentation using the SuPreM model. This demo allows users to upload CT scans in NIfTI format (.nii.gz) and receive automated organ segmentation results.

**Developed for Johns Hopkins CCVL Lab - Project II Application**

## 🎯 Purpose

This demo showcases the ability to integrate AI-based medical imaging models into web applications, specifically:
- File upload handling for medical imaging data
- Docker-based AI model execution (SuPreM segmentation)
- Medical image visualization and result presentation
- User-friendly interface for non-technical users

## 🚀 Features

- **Easy Upload**: Drag & drop interface for .nii.gz CT scan files
- **AI Processing**: Automated segmentation using SuPreM AI model in Docker
- **Real-time Status**: Live updates during processing
- **Visual Results**: Preview segmented organs with interactive image viewer
- **Download Results**: Complete segmentation files in ZIP format
- **Responsive Design**: Bootstrap-based UI that works on desktop and mobile

## 🛠 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | Flask (Python) | Web server, file handling, Docker integration |
| **Frontend** | HTML5 + Bootstrap 5 + JavaScript | User interface and interactions |
| **AI Engine** | SuPreM model via Docker | Medical image segmentation |
| **Image Processing** | nibabel + matplotlib | NIfTI file handling and visualization |
| **Storage** | Local filesystem | Temporary file storage |

## 📋 Prerequisites

Before running this application, ensure you have:

1. **Python 3.8+** with pip
2. **Docker** installed and running
3. **SuPreM Docker image** (qchen99/suprem:v1)
4. **GPU support** (recommended for faster processing)

### Installing Docker and SuPreM Model

```bash
# Install Docker (macOS with Homebrew)
brew install docker

# Start Docker Desktop
open -a Docker

# Pull the SuPreM model (this may take some time - ~5GB)
docker pull qchen99/suprem:v1

# Verify the image is available
docker images | grep suprem
```

## 🔧 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/sshhaawwnn111/BodyMaps-Demo.git
cd BodyMaps-Demo
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create Required Directories

```bash
mkdir -p inputs_data outputs_data static/results
```

### 5. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## 🖥 Usage

### 1. Upload CT Scan
- Navigate to `http://localhost:5000`
- Drag and drop a .nii.gz file or click "Browse Files"
- Supported format: NIfTI compressed (.nii.gz)

### 2. Monitor Processing
- File upload triggers automatic processing
- Real-time status updates show progress
- Processing typically takes 5-15 minutes depending on:
  - CT scan size and complexity
  - System performance (GPU vs CPU)
  - Available memory

### 3. View Results
- Preview segmented organs in the web interface
- Download complete results as ZIP file
- Results include:
  - Individual organ segmentations (.nii.gz)
  - Combined labels file
  - Preview images (.png)

## 📁 Project Structure

```
BodyMaps-Demo/
│
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── templates/                  # HTML templates
│   ├── upload.html            # Main upload interface
│   └── results.html           # Results display page
│
├── utils/                      # Utility functions
│   └── nii_to_png.py          # NIfTI to PNG conversion
│
├── static/                     # Static files
│   └── results/               # Generated preview images
│       └── casename00001/     # Results for each case
│
├── inputs_data/               # Uploaded CT scans
│   └── casename00001/         # Auto-generated case directories
│       └── ct.nii.gz         # Uploaded CT scan
│
└── outputs_data/              # SuPreM segmentation results
    └── casename00001/         # Results for each case
        └── segmentations/     # Segmented organ files
            ├── liver.nii.gz
            ├── kidney_left.nii.gz
            ├── kidney_right.nii.gz
            └── combined_labels.nii.gz
```

## 🐳 SuPreM Docker Integration

The application uses the SuPreM model through Docker with the following command:

```bash
docker container run --gpus "device=0" -m 128G --rm \
  -v inputs_data:/workspace/inputs/ \
  -v outputs_data:/workspace/outputs/ \
  qchen99/suprem:v1 /bin/bash -c "sh predict.sh"
```

### Command Breakdown:
- `--gpus "device=0"`: Use GPU for acceleration
- `-m 128G`: Allocate 128GB memory (adjust based on your system)
- `--rm`: Remove container after execution
- `-v inputs_data:/workspace/inputs/`: Mount input directory
- `-v outputs_data:/workspace/outputs/`: Mount output directory
- `qchen99/suprem:v1`: SuPreM Docker image
- `sh predict.sh`: Execute segmentation script

## 🔍 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Main upload page |
| `/upload` | POST | Handle file upload |
| `/status/<case_name>` | GET | Get processing status |
| `/results/<case_name>` | GET | View results page |
| `/download/<case_name>` | GET | Download results ZIP |

## 🧪 Testing

### Sample Data
You can test the application with medical imaging sample data:
- Use publicly available NIfTI CT scan files
- Ensure files are in .nii.gz format
- Typical file sizes: 50-500MB

### Local Testing
```bash
# Test file upload
curl -X POST -F "file=@sample_ct.nii.gz" http://localhost:5000/upload

# Check processing status
curl http://localhost:5000/status/casename00001
```

## 🔧 Troubleshooting

### Common Issues

1. **Docker not found**
   ```
   Error: Docker command not found
   Solution: Install Docker and ensure it's in your PATH
   ```

2. **GPU not available**
   ```
   Error: GPU device not found
   Solution: Remove --gpus flag or install NVIDIA Docker support
   ```

3. **Memory issues**
   ```
   Error: Out of memory
   Solution: Reduce -m parameter or increase system memory
   ```

4. **Port already in use**
   ```
   Error: Port 5000 already in use
   Solution: Change port in app.py or kill existing process
   ```

### Debug Mode
Run with debug logging:
```bash
export FLASK_DEBUG=1
python app.py
```

## 🔮 Future Enhancements

- **Multiple File Support**: Batch processing of multiple CT scans
- **User Authentication**: Secure file upload and result access
- **Cloud Deployment**: AWS/GCP deployment with scalable processing
- **Advanced Visualization**: 3D rendering and interactive viewers
- **Model Options**: Support for multiple segmentation models
- **API Integration**: RESTful API for programmatic access

## 📸 Screenshots

### Main Upload Interface
![Upload Interface](docs/upload_interface.png)

### Processing Status
![Processing Status](docs/processing_status.png)

### Results Display
![Results Display](docs/results_display.png)

## 👨‍💻 Development

### Adding New Models
To integrate additional segmentation models:
1. Update Docker commands in `app.py`
2. Modify file processing in `utils/nii_to_png.py`
3. Update UI to reflect new capabilities

### Customizing UI
- Modify templates in `templates/` directory
- Update styling in HTML `<style>` sections
- Add new static files in `static/` directory

## 📄 License

This project is developed for educational and demonstration purposes as part of the Johns Hopkins CCVL Lab application process.

## 🤝 Contributing

This is a demo application for a specific application process. For questions or suggestions, please contact the developer.

## 📞 Contact

**Developer**: Shawn Wang  
**Purpose**: Johns Hopkins CCVL Lab - Project II Application  
**Date**: January 2025

---

**Note**: This is a prototype demonstration application. For production use, additional security measures, error handling, and performance optimizations would be required.