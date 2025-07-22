# BodyMaps SuPreM Segmentation Demo

A web-based application for AI-powered medical image segmentation using the SuPreM model. This demo allows users to upload CT scans in NIfTI format (.nii.gz) and receive automated organ segmentation results.

**Developed for Johns Hopkins CCVL Lab - Project II Application**

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

## 📄 License

This project is developed for educational and demonstration purposes as part of the Johns Hopkins CCVL Lab application process.

## 📞 Contact

**Developer**: Shawn Wang  
**Purpose**: Johns Hopkins CCVL Lab - Project II Application  
**Date**: July 2025

---

**Note**: This is a prototype demonstration application. For production use, additional security measures, error handling, and performance optimizations would be required.