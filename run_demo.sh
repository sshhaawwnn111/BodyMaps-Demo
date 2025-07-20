#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development

# Run the application
echo "🚀 Starting BodyMaps Demo..."
echo "📱 Open your browser to: http://localhost:5000"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

python app.py
