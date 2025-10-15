from rembg import remove, new_session
from PIL import Image
import io
import time
import logging
import gc

logger = logging.getLogger(__name__)

class RembgAPIService:
    """REMBG API Service"""
    
    def __init__(self):
        self.sessions = {}
        self.model_descriptions = {
            'u2net': 'Standard Model (best balance)',
            'silueta': 'Compact Model (faster, 43MB)',
            'u2net_human_seg': 'Specifically for humans',
            'isnet-general-use': 'Improved Model (latest version)'
        }
        self._initialize_models()
    
    def _initialize_models(self):
        """Load models at startup"""
        logger.info("🚀 Starting REMBG API...")
        
        models_to_load = ['u2net', 'silueta', 'u2net_human_seg', 'isnet-general-use']
        
        for model_name in models_to_load:
            try:
                logger.info(f"Loading {model_name}...")
                self.sessions[model_name] = new_session(model_name)
                logger.info(f"✅ {model_name} successfully loaded")
            except Exception as e:
                logger.warning(f"⚠️ {model_name} not loaded - {e}")
        
        logger.info(f"🎉 API ready! Available models: {list(self.sessions.keys())}")
    
    def process_image(self, image_file, model_name='u2net', max_size=None):
        """Process image"""
        start_time = time.time()
        
        try:
            image = Image.open(image_file.stream)
            original_size = image.size
            
            logger.info(f"📸 Original image size: {original_size}")
            
            if model_name not in self.sessions:
                logger.warning(f"Model '{model_name}' not available, using 'u2net'")
                model_name = 'u2net'
            
            session = self.sessions[model_name]
            
            gc.collect()
            
            logger.info(f"🤖 Processing with {model_name}...")
            result = remove(image, session=session)
            
            output = io.BytesIO()
            result.save(output, format='PNG')
            output.seek(0)
            
            processing_time = time.time() - start_time
            
            logger.info(f"✅ Processing completed in {processing_time:.2f}s")
            
            del image, result
            gc.collect()
            
            return output, processing_time, model_name
            
        except Exception as e:
            logger.error(f"❌ Processing error: {e}")
            gc.collect()
            raise 