#!/bin/bash

# Start script for React version of BodyMaps Demo

echo "🚀 Starting BodyMaps SuPreM Segmentation Demo (React Version)"

# Check if build directory exists
if [ ! -d "build" ]; then
    echo "📦 Build directory not found. Building React app..."
    npm run build
fi

# Check if required directories exist
mkdir -p inputs_data outputs_data static/results static/segmentation_preview

# Start the Flask server
echo "🌐 Starting Flask server with React frontend..."
echo "📍 Access the application at: http://localhost:5001"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

python app_react.py