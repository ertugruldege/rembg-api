from flask import Flask
from flask_cors import CORS
import os
import logging
import psutil

# Import services and routes
from services.rembg_service import RembgAPIService
from routes.api import api_bp, register_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Initialize service
rembg_service = RembgAPIService()

# Register routes
register_routes(rembg_service)
app.register_blueprint(api_bp)

# Application configuration
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    # Startup information
    memory_info = psutil.virtual_memory()
    logger.info(f"🚀 Starting REMBG API v2.0 on port {port}")
    logger.info(f"💾 Available RAM: {memory_info.total / (1024**3):.1f}GB")
    
    app.run(
        host='0.0.0.0', 
        port=port, 
        debug=debug_mode
    ) 