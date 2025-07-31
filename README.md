# BodyMaps SuPreM Segmentation Demo

A web-based application for AI-powered medical image segmentation using the SuPreM model. This demo allows users to upload CT scans in NIfTI format (.nii.gz) and receive automated organ segmentation results.

**Developed for Johns Hopkins CCVL Lab - Project II Application**

## 🚀 Features

- **Easy Upload**: Drag & drop interface for .nii.gz CT scan files
- **AI Processing**: Automated segmentation using SuPreM AI model in Docker
- **Real-time Status**: Live updates during processing
- **Visual Results**: Preview segmented organs with interactive image viewer
- **Interactive Segmentation**: Real-time organ segmentation with nnInteractive AI
- **Download Results**: Complete segmentation files in ZIP format
- **Responsive Design**: Bootstrap-based UI that works on desktop and mobile

## 🛠 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | Flask (Python) | Web server, file handling, Docker integration |
| **Frontend** | React + Bootstrap 5 + JavaScript | Modern SPA user interface |
| **AI Engine** | SuPreM model via Docker | Medical image segmentation |
| **Image Processing** | nibabel + matplotlib | NIfTI file handling and visualization |
| **Storage** | Local filesystem | Temporary file storage |

### 🔄 Frontend Options

This application now supports **two frontend implementations**:

1. **React Frontend** (Recommended) - Modern SPA with React components and interactive segmentation

## 📋 Prerequisites

Before running this application, ensure you have:

1. **Python 3.8+** with pip
2. **Node.js 16+** and npm (for React frontend)
3. **Docker** installed and running
4. **SuPreM Docker image** (qchen99/suprem:v1)

## 📁 Project Structure

```
BodyMaps-Demo/
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── UploadPage.js  # Main upload interface
│   │   │   └── ResultsPage.js # Results display page
│   │   ├── App.js             # Main React app
│   │   └── index.js           # React entry point
│   ├── public/                # Public assets
│   ├── package.json           # Node.js dependencies
│   └── build/                 # Production build (generated)
│
├── backend/                    # Flask backend API
│   ├── app.py                 # Main Flask application
│   ├── requirements.txt       # Python dependencies
│   ├── utils/                 # Utility functions
│   │   └── nii_to_png.py     # NIfTI to PNG conversion
│   ├── inputs_data/          # Uploaded CT scans
│   ├── outputs_data/         # SuPreM segmentation results
│   └── static/               # Static files and results
│
├── setup.sh         # Setup script for separated structure
├── start_react_app.sh              # Development mode (both servers)
└── README.md                 # This file
```

## 📄 License

This project is developed for educational and demonstration purposes as part of the Johns Hopkins CCVL Lab application process.

## 📞 Contact

**Developer**: Shawn Wang  
**Purpose**: Johns Hopkins CCVL Lab - Project II Application  
**Date**: July 2025

---

**Note**: This is a prototype demonstration application. For production use, additional security measures, error handling, and performance optimizations would be required.