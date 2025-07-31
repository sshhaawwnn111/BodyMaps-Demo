#!/bin/bash

# Setup script for separated frontend/backend structure

echo "🚀 Setting up BodyMaps Demo with separated frontend/backend..."

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+ first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ Python version: $(python --version)"
echo "✅ Docker version: $(docker --version)"

# Setup backend
echo ""
echo "🐍 Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create required directories
echo "📁 Creating required directories..."
mkdir -p inputs_data outputs_data static/results static/segmentation_preview

# Test the modular structure
echo "🧪 Testing modular backend structure..."
python -c "
try:
    from api.upload import upload_bp
    from api.processing import processing_bp
    from api.results import results_bp
    from api.imaging import imaging_bp
    from config import config
    print('✅ All API modules imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

cd ..

# Setup frontend
echo ""
echo "⚛️ Setting up frontend..."
cd frontend

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Build the React app
echo "🔨 Building React application..."
npm run build

cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Start the backend (in one terminal):"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "2. Start the frontend (in another terminal):"
echo "   cd frontend"
echo "   npm start"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔗 Backend API: http://localhost:5001"
echo ""
echo "💡 The frontend will automatically proxy API calls to the backend."