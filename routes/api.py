from flask import Blueprint, request, send_file, jsonify
import logging
import base64

logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__)

def register_routes(rembg_service, withoutbg_service):
    """Register all API routes with the services"""
    
    @api_bp.route('/', methods=['GET'])
    def health_check():
        """Health Check and API-Info"""
        return jsonify({
            "status": "online",
            "service": "REMBG API",
            "version": "2.0",
            "available_providers": ["rembg", "withoutbg"],
            "available_models": list(rembg_service.sessions.keys()),
            "endpoints": {
                "remove_background": "/remove-bg",
                "batch_process": "/batch",
                "models": "/models",
                "health": "/",
                "system": "/system"
            },
            "usage": {
                "single_image": "POST /remove-bg with 'image' file",
                "provider_selection": "Add 'provider' parameter (rembg, withoutbg) - default: rembg",
                "model_selection": "Add 'model' parameter (u2net, silueta, human) - only for rembg",
                "size_limit": "Add 'max_size' parameter (default: 2000px)",
                "supported_formats": "JPG, PNG, WebP, TIFF"
            },
            "limits": {
                "max_image_size": "40MB",
                "batch_processing": "unlimited"
            }
        })
    
    @api_bp.route('/system', methods=['GET'])
    def system_info():
        """Detailed System Information"""
        return jsonify({
            "system": {
                "loaded_models": list(rembg_service.sessions.keys()),
                "model_count": len(rembg_service.sessions)
            },
            "capabilities": {
                "max_file_size": "40MB",
                "max_resolution": "unlimited",
                "batch_processing": "unlimited",
                "output_quality": "maximum"
            }
        })
    
    @api_bp.route('/models', methods=['GET'])
    def get_available_models():
        """Available models and descriptions"""
        provider = request.args.get('provider', 'rembg')
        
        if provider == 'withoutbg':
            return jsonify({
                "provider": "withoutbg",
                "available_models": ["snap"],
                "default": "snap",
                "note": "Withoutbg uses the Snap model (local processing)",
                "model_info": {
                    "snap": {"speed": "fast", "quality": "high", "description": "Open source background removal model"}
                }
            })
        else:
            available_models = {}
            for model_name in rembg_service.sessions.keys():
                available_models[model_name] = rembg_service.model_descriptions.get(
                    model_name, "AI Model for Background-Removal"
                )
            
            return jsonify({
                "provider": "rembg",
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
            provider = request.form.get('provider', 'rembg')
            model = request.form.get('model', 'u2net')
            max_size = int(request.form.get('max_size', 2000))
            
            # Select service based on provider
            if provider == 'withoutbg':
                service = withoutbg_service
            else:
                service = rembg_service
            
            file_size_mb = len(file.read()) / (1024 * 1024)
            file.seek(0)
            
            if file_size_mb > 40:
                return jsonify({
                    'error': f'File too large: {file_size_mb:.1f}MB',
                    'limit': 'Maximum: 40MB'
                }), 413
            
            logger.info(f"📁 New request: {file.filename} ({file_size_mb:.1f}MB), Provider: {provider}, Model: {model}, Max-Size: {max_size}")
            
            # Process image
            result_image, processing_time, used_model = service.process_image(
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
            response.headers['X-Provider-Used'] = provider
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
            
            # Read parameters
            provider = request.form.get('provider', 'rembg')
            model = request.form.get('model', 'u2net')
            
            # Select service based on provider
            if provider == 'withoutbg':
                service = withoutbg_service
            else:
                service = rembg_service
            
            results = []
            total_time = 0
            
            logger.info(f"📦 Batch processing: {len(files)} images with Provider: {provider}, Model: {model}")
            
            for i, file in enumerate(files):
                try:
                    result_image, proc_time, used_model = service.process_image(file, model)
                    total_time += proc_time
                    
                    # As Base64 for JSON-Response
                    img_b64 = base64.b64encode(result_image.getvalue()).decode()
                    
                    results.append({
                        'index': i,
                        'filename': file.filename,
                        'success': True,
                        'processing_time': f"{proc_time:.2f}s",
                        'provider_used': provider,
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