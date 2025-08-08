from flask import Blueprint, request, send_file, jsonify
import psutil
import logging
import base64

logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__)

def register_routes(rembg_service):
    """Register all API routes with the service"""
    
    @api_bp.route('/', methods=['GET'])
    def health_check():
        """Health Check and API-Info"""
        memory_info = rembg_service.get_memory_info()
        
        return jsonify({
            "status": "online",
            "service": "REMBG API",
            "version": "2.0",
            "available_models": list(rembg_service.sessions.keys()),
            "system_info": {
                "total_memory_gb": memory_info.get('total_gb'),
                "memory_usage_percent": memory_info.get('used_percent'),
                "available_memory_gb": memory_info.get('available_gb')
            },
            "endpoints": {
                "remove_background": "/remove-bg",
                "batch_process": "/batch",
                "models": "/models",
                "health": "/",
                "system": "/system"
            },
            "usage": {
                "single_image": "POST /remove-bg with 'image' file",
                "model_selection": "Add 'model' parameter (u2net, silueta, human)",
                "size_limit": "Add 'max_size' parameter (default: 2000px)",
                "supported_formats": "JPG, PNG, WebP, TIFF"
            },
            "limits": {
                "max_image_size": f"{rembg_service._get_max_file_size(psutil.virtual_memory().available / (1024**3))}MB (dynamic)",
                "batch_processing": f"{rembg_service._get_max_batch_size(psutil.virtual_memory().available / (1024**3))} images (dynamic)",
                "max_resolution": "Dynamic based on RAM",
                "available_ram_gb": round(psutil.virtual_memory().available / (1024**3), 1)
            }
        })
    
    @api_bp.route('/system', methods=['GET'])
    def system_info():
        """Detailed System Information for Debugging"""
        memory_info = rembg_service.get_memory_info()
        
        return jsonify({
            "system": {
                "memory": memory_info,
                "loaded_models": list(rembg_service.sessions.keys()),
                "model_count": len(rembg_service.sessions)
            },
            "performance": {
                "can_handle_large_images": memory_info.get('total_gb', 0) > 16,
                "recommended_max_size": 2000 if memory_info.get('total_gb', 0) > 16 else 1500,
                "batch_limit": 10 if memory_info.get('total_gb', 0) > 16 else 3
            }
        })
    
    @api_bp.route('/models', methods=['GET'])
    def get_available_models():
        """Available models and descriptions"""
        available_models = {}
        for model_name in rembg_service.sessions.keys():
            available_models[model_name] = rembg_service.model_descriptions.get(
                model_name, "AI Model for Background-Removal"
            )
        
        return jsonify({
            "available_models": available_models,
            "default": "u2net",
            "recommendations": {
                "general": "u2net",
                "fast": "silueta", 
                "people": "u2net_human_seg",
                "high_quality": "isnet-general-use"
            },
            "model_info": {
                "u2net": {"size": "176MB", "speed": "medium", "quality": "high"},
                "silueta": {"size": "43MB", "speed": "fast", "quality": "good"},
                "u2net_human_seg": {"size": "176MB", "speed": "medium", "quality": "excellent for humans"}
            }
        })
    
    @api_bp.route('/remove-bg', methods=['POST'])
    def remove_background():
        """Main endpoint for Background-Removal"""
        try:
            # Input validation
            if 'image' not in request.files:
                return jsonify({
                    'error': 'No image found',
                    'hint': 'Send the image as "image" parameter'
                }), 400
            
            file = request.files['image']
            
            if file.filename == '':
                return jsonify({'error': 'Empty file'}), 400
            
            # Read parameters
            model = request.form.get('model', 'u2net')
            max_size = int(request.form.get('max_size', 2000))
            
            # File-Size Check based on available RAM
            file_size_mb = len(file.read()) / (1024 * 1024)
            file.seek(0)  # Reset file pointer
            
            available_ram_gb = psutil.virtual_memory().available / (1024**3)
            max_file_size = rembg_service._get_max_file_size(available_ram_gb)
            
            if file_size_mb > max_file_size:
                return jsonify({
                    'error': f'File too large: {file_size_mb:.1f}MB',
                    'limit': f'Maximum: {max_file_size}MB (based on {available_ram_gb:.1f}GB available RAM)'
                }), 413
            
            logger.info(f"📁 New request: {file.filename} ({file_size_mb:.1f}MB), Model: {model}, Max-Size: {max_size}")
            
            # Process image
            result_image, processing_time, used_model = rembg_service.process_image(
                file, model, max_size
            )
            
            # Response with extended metadata
            response = send_file(
                result_image,
                mimetype='image/png',
                as_attachment=False,
                download_name=f'removed_bg_{file.filename.rsplit(".", 1)[0]}.png'
            )
            
            # Extended Headers
            response.headers['X-Processing-Time'] = f"{processing_time:.2f}s"
            response.headers['X-Model-Used'] = used_model
            response.headers['X-Service'] = 'REMBG API v2.0'
            response.headers['X-File-Size-MB'] = f"{file_size_mb:.1f}"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ API Error: {e}")
            return jsonify({
                'error': f'Processing error: {str(e)}',
                'status': 'failed',
                'hint': 'Try a smaller image or different model'
            }), 500
    
    @api_bp.route('/batch', methods=['POST'])
    def batch_process():
        """Batch processing"""
        try:
            files = request.files.getlist('images')
            
            if not files or len(files) == 0:
                return jsonify({'error': 'No images found'}), 400
            
            # Dynamic batch limit based on available RAM
            available_ram_gb = psutil.virtual_memory().available / (1024**3)
            max_batch_size = rembg_service._get_max_batch_size(available_ram_gb)
            
            if len(files) > max_batch_size:
                return jsonify({
                    'error': f'Too many images: {len(files)}',
                    'limit': f'Maximum: {max_batch_size} images (based on {available_ram_gb:.1f}GB available RAM)'
                }), 400
            
            model = request.form.get('model', 'u2net')
            results = []
            total_time = 0
            
            logger.info(f"📦 Batch processing: {len(files)} images with {model}")
            
            for i, file in enumerate(files):
                try:
                    result_image, proc_time, used_model = rembg_service.process_image(file, model)
                    total_time += proc_time
                    
                    # As Base64 for JSON-Response
                    img_b64 = base64.b64encode(result_image.getvalue()).decode()
                    
                    results.append({
                        'index': i,
                        'filename': file.filename,
                        'success': True,
                        'processing_time': f"{proc_time:.2f}s",
                        'model_used': used_model,
                        'image_data': f"data:image/png;base64,{img_b64}"
                    })
                    
                except Exception as e:
                    logger.error(f"Batch processing failed for {file.filename}: {e}")
                    results.append({
                        'index': i,
                        'filename': file.filename,
                        'success': False,
                        'error': str(e)
                    })
            
            return jsonify({
                'batch_results': {
                    'total_images': len(files),
                    'successful': len([r for r in results if r.get('success')]),
                    'failed': len([r for r in results if not r.get('success')]),
                    'total_time': f"{total_time:.2f}s",
                    'average_time': f"{total_time/len(files):.2f}s"
                },
                'results': results
            })
            
        except Exception as e:
            logger.error(f"❌ Batch Error: {e}")
            return jsonify({'error': f'Batch processing error: {str(e)}'}), 500 