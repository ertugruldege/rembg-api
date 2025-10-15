from withoutbg import remove_background
from PIL import Image
import io
import time
import logging
import gc

logger = logging.getLogger(__name__)

class WithoutbgService:
    """Withoutbg API Service"""
    
    def __init__(self):
        self.provider_name = 'withoutbg'
        logger.info("🚀 Withoutbg Service initialized (Local Processing)")
    
    def process_image(self, image_file, model_name='snap', max_size=None):
        """Process image with Withoutbg"""
        start_time = time.time()
        
        try:
            image = Image.open(image_file.stream)
            original_size = image.size
            
            logger.info(f"📸 Original image size: {original_size}")
            
            logger.info(f"🤖 Processing with Withoutbg (Snap model)...")
            result = remove_background(image)
            
            output = io.BytesIO()
            result.save(output, format='PNG')
            output.seek(0)
            
            processing_time = time.time() - start_time
            
            logger.info(f"✅ Processing completed in {processing_time:.2f}s")
            
            del image, result
            gc.collect()
            
            return output, processing_time, 'snap'
            
        except Exception as e:
            logger.error(f"❌ Processing error: {e}")
            gc.collect()
            raise

