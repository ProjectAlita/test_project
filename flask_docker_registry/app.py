"""
Main application module for Flask Docker Registry
"""

import os
from flask import Flask, jsonify, request


def create_app(config=None):
    """
    Create and configure the Flask application
    
    Args:
        config: Configuration object or dictionary
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Default configuration
    app.config.update(dict(
        STORAGE_PATH=os.environ.get('STORAGE_PATH', os.path.join(os.getcwd(), 'storage')),
        AUTH_ENABLED=os.environ.get('AUTH_ENABLED', 'true').lower() == 'true',
        AUTH_USER=os.environ.get('AUTH_USER', 'admin'),
        AUTH_PASSWORD=os.environ.get('AUTH_PASSWORD', 'password'),
        AUTH_TOKEN_EXPIRY=int(os.environ.get('AUTH_TOKEN_EXPIRY', '3600')),  # 1 hour
    ))
    
    # Update config if provided
    if config:
        app.config.update(config)
    
    # Create storage directory if it doesn't exist
    os.makedirs(app.config['STORAGE_PATH'], exist_ok=True)
    
    # Register blueprints
    from flask_docker_registry.api.v2 import bp as api_v2_bp
    app.register_blueprint(api_v2_bp)
    
    @app.route('/')
    def index():
        return jsonify({
            "name": "Flask Docker Registry",
            "description": "Docker Registry HTTP API v2 implementation using Flask"
        })
    
    return app