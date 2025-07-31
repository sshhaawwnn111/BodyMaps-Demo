"""
Main Flask application
Modular backend with separated API endpoints
"""

import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from config import config

# Global variables for processing status
processing_status = {}

def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Enable CORS for React frontend
    CORS(app)
    
    # Initialize configuration
    config[config_name].init_app(app)
    
    # Register blueprints
    from api.upload import upload_bp
    from api.processing import processing_bp
    from api.results import results_bp
    from api.imaging import imaging_bp
    
    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(processing_bp, url_prefix='/api')
    app.register_blueprint(results_bp, url_prefix='/api')
    app.register_blueprint(imaging_bp, url_prefix='/api')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'Backend is running'})
    
    # Serve static files (for backward compatibility)
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory('static', filename)
    
    # Serve React build files (for production mode)
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_static_files(path):
        if path != '' and os.path.exists(os.path.join('static/build', path)):
            return send_from_directory('static/build', path)
        elif os.path.exists('static/build/index.html'):
            return send_from_directory('static/build', 'index.html')
        else:
            return jsonify({'message': 'API server running. Frontend not built yet.'}), 200
    
    return app

# Create app instance
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)