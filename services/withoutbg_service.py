from withoutbg import remove_background
from PIL import Image
import io
import time
import logging
import gc
import psutil

logger = logging.getLogger(__name__)

class WithoutbgService:
    """Withoutbg API Service"""
    
    def __init__(self):
        self.provider_name = 'withoutbg'
        logger.info("🚀 Withoutbg Service initialized (Local Processing)")
    
    def _get_max_pixels(self, available_ram_gb):
        """Get max pixels based on available RAM"""
        if available_ram_gb > 8:
            return 8000000
        elif available_ram_gb > 4:
            return 6000000
        elif available_ram_gb > 2:
            return 4000000
        else:
            return 2000000
    
    def _get_max_file_size(self, available_ram_gb):
        """Get max file size based on available RAM"""
        if available_ram_gb > 8:
            return 50
        elif available_ram_gb > 4:
            return 30
        elif available_ram_gb > 2:
            return 20
        else:
            return 10
    
    def _get_max_batch_size(self, available_ram_gb):
        """Get max batch size based on available RAM"""
        if available_ram_gb > 8:
            return 20
        elif available_ram_gb > 4:
            return 15
        elif available_ram_gb > 2:
            return 10
        else:
            return 5
    
    def get_memory_info(self):
        """Current Memory Information for Debugging"""
        try:
            memory = psutil.virtual_memory()
            return {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_percent': round(memory.percent, 1)
            }
        except:
            return {'error': 'Memory info not available'}
    
    def process_image(self, image_file, model_name='snap', max_size=2000):
        """Process image with Withoutbg"""
        start_time = time.time()
        
        try:
            memory_before = psutil.virtual_memory().percent
            
            image = Image.open(image_file.stream)
            original_size = image.size
            original_pixels = original_size[0] * original_size[1]
            
            logger.info(f"📸 Original image size: {original_size} ({original_pixels:,} pixels)")
            
            available_ram_gb = psutil.virtual_memory().available / (1024**3)
            max_pixels = self._get_max_pixels(available_ram_gb)
            
            logger.info(f"💾 Available RAM: {available_ram_gb:.1f}GB, Max pixels: {max_pixels:,}")
            
            if original_pixels > max_pixels:
                scale_factor = (max_pixels / original_pixels) ** 0.5
                new_width = int(original_size[0] * scale_factor)
                new_height = int(original_size[1] * scale_factor)
                
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.info(f"🔄 Intelligent scaling: {original_size} → {image.size}")
            elif max(image.size) > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                logger.info(f"📏 Standard reduction: {original_size} → {image.size}")
            
            gc.collect()
            
            logger.info(f"🤖 Processing with Withoutbg (Snap model)...")
            result = remove_background(image)
            
            output = io.BytesIO()
            result.save(output, format='PNG', optimize=True, compress_level=9)
            output.seek(0)
            
            processing_time = time.time() - start_time
            memory_after = psutil.virtual_memory().percent
            
            logger.info(f"✅ Processing completed in {processing_time:.2f}s")
            logger.info(f"💾 Memory: {memory_before:.1f}% → {memory_after:.1f}%")
            
            del image, result
            gc.collect()
            
            return output, processing_time, 'snap'
            
        except Exception as e:
            logger.error(f"❌ Processing error: {e}")
            gc.collect()
            raise

