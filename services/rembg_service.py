from rembg import remove, new_session
from PIL import Image
import io
import time
import logging
import gc
import psutil

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
    
    def _get_max_pixels(self, available_ram_gb):
        """Get max pixels based on available RAM"""
        if available_ram_gb > 8:
            return 8000000  # 8GB+ RAM: 8M pixels
        elif available_ram_gb > 4:
            return 6000000  # 4-8GB RAM: 6M pixels
        elif available_ram_gb > 2:
            return 4000000  # 2-4GB RAM: 4M pixels
        else:
            return 2000000  # <2GB RAM: 2M pixels
    
    def _get_max_file_size(self, available_ram_gb):
        """Get max file size based on available RAM"""
        if available_ram_gb > 8:
            return 50  # 8GB+ RAM: 50MB
        elif available_ram_gb > 4:
            return 30  # 4-8GB RAM: 30MB
        elif available_ram_gb > 2:
            return 20  # 2-4GB RAM: 20MB
        else:
            return 10  # <2GB RAM: 10MB
    
    def _get_max_batch_size(self, available_ram_gb):
        """Get max batch size based on available RAM"""
        if available_ram_gb > 8:
            return 20  # 8GB+ RAM: 20 images
        elif available_ram_gb > 4:
            return 15  # 4-8GB RAM: 15 images
        elif available_ram_gb > 2:
            return 10  # 2-4GB RAM: 10 images
        else:
            return 5   # <2GB RAM: 5 images
    
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
    
    def _initialize_models(self):
        """Load models at startup"""
        logger.info("🚀 Starting REMBG API...")
        
        # Memory-Check before Model-Loading
        memory_info = self.get_memory_info()
        logger.info(f"💾 Available RAM: {memory_info.get('total_gb', 'N/A')}GB")
        
        # Load all available models
        models_to_load = ['u2net', 'silueta', 'u2net_human_seg', 'isnet-general-use']
        
        for model_name in models_to_load:
            try:
                logger.info(f"Loading {model_name}...")
                self.sessions[model_name] = new_session(model_name)
                logger.info(f"✅ {model_name} successfully loaded")
            except Exception as e:
                logger.warning(f"⚠️ {model_name} not loaded - {e}")
        
        logger.info(f"🎉 API ready! Available models: {list(self.sessions.keys())}")
        
        # Final Memory-Check
        final_memory = self.get_memory_info()
        logger.info(f"💾 After Model-Loading: {final_memory.get('used_percent', 'N/A')}% RAM used")
    
    def process_image(self, image_file, model_name='u2net', max_size=2000):
        """Process image"""
        start_time = time.time()
        
        try:
            # Pre-processing Memory-Check
            memory_before = psutil.virtual_memory().percent
            
            # Load image
            image = Image.open(image_file.stream)
            original_size = image.size
            original_pixels = original_size[0] * original_size[1]
            
            logger.info(f"📸 Original image size: {original_size} ({original_pixels:,} pixels)")
            
            # Get RAM-based limits
            available_ram_gb = psutil.virtual_memory().available / (1024**3)
            max_pixels = self._get_max_pixels(available_ram_gb)
            
            logger.info(f"💾 Available RAM: {available_ram_gb:.1f}GB, Max pixels: {max_pixels:,}")
            
            # Intelligent size adjustment
            if original_pixels > max_pixels:
                # Calculate optimal size based on pixel count
                scale_factor = (max_pixels / original_pixels) ** 0.5
                new_width = int(original_size[0] * scale_factor)
                new_height = int(original_size[1] * scale_factor)
                
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.info(f"🔄 Intelligent scaling: {original_size} → {image.size}")
            elif max(image.size) > max_size:
                # Fallback: Standard thumbnail
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                logger.info(f"📏 Standard reduction: {original_size} → {image.size}")
            
            # Select model with fallback
            if model_name not in self.sessions:
                logger.warning(f"Model '{model_name}' not available, using 'u2net'")
                model_name = 'u2net'
            
            session = self.sessions[model_name]
            
            # Memory cleanup before AI-Processing
            gc.collect()
            
            # Remove background
            logger.info(f"🤖 Processing with {model_name}...")
            result = remove(image, session=session)
            
            # Optimized PNG output with better compression
            output = io.BytesIO()
            result.save(output, format='PNG', optimize=True, compress_level=9)
            output.seek(0)
            
            processing_time = time.time() - start_time
            memory_after = psutil.virtual_memory().percent
            
            logger.info(f"✅ Processing completed in {processing_time:.2f}s")
            logger.info(f"💾 Memory: {memory_before:.1f}% → {memory_after:.1f}%")
            
            # Memory cleanup
            del image, result
            gc.collect()
            
            return output, processing_time, model_name
            
        except Exception as e:
            logger.error(f"❌ Processing error: {e}")
            # Emergency cleanup
            gc.collect()
            raise 