from flask import Flask
from flask_cors import CORS
import os
import logging

# Import services and routes
from services.rembg_service import RembgAPIService
from services.withoutbg_service import WithoutbgService
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

# Initialize services
rembg_service = RembgAPIService()
withoutbg_service = WithoutbgService()

# Register routes
register_routes(rembg_service, withoutbg_service)
app.register_blueprint(api_bp)

# Application configuration
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    # Startup information
    logger.info(f"🚀 Starting REMBG API v2.0 on port {port}")
    logger.info(f"⚡ Maximum quality mode enabled - No resolution limits")
    
    app.run(
        host='0.0.0.0', 
        port=port, 
        debug=debug_mode
    ) 