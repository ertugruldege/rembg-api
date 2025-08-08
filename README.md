# REMBG API

A high-performance REST API for background removal using REMBG library. Remove backgrounds from images with multiple AI models.

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/ertugruldege/rembg-api.git
cd rembg-api
pip install -r requirements.txt
python app.py
```

API will be available at `http://localhost:5000`

## 📡 API Endpoints

### Health Check

```http
GET /
```

### Remove Background

```http
POST /remove-bg
Content-Type: multipart/form-data

Parameters:
- image: Image file (required)
- model: AI model (optional, default: u2net)
- max_size: Max image size (optional, default: 2000px)
```

### Batch Processing

```http
POST /batch
Content-Type: multipart/form-data

Parameters:
- images: Multiple image files (required)
- model: AI model (optional, default: u2net)
```

### Get Models

```http
GET /models
```

### System Info

```http
GET /system
```

## 🤖 AI Models

| Model               | Description                   | Size  | Speed  | Quality   |
| ------------------- | ----------------------------- | ----- | ------ | --------- |
| `u2net`             | Standard model (best balance) | 176MB | Medium | High      |
| `silueta`           | Compact model (fast)          | 44MB  | Fast   | Good      |
| `u2net_human_seg`   | Specifically for humans       | 176MB | Medium | Excellent |
| `isnet-general-use` | Improved model (latest)       | 179MB | Medium | High      |

## ⚙️ Configuration

### Environment Variables

Copy `env.example` to `.env` and configure:

```bash
cp env.example .env
```

**Required:**

- `PORT`: Application port (default: 5000)
- `FLASK_ENV`: Flask environment (development/production)

### Dynamic Limits

API limits are automatically adjusted based on available RAM:

| RAM   | File Size | Batch Limit | Max Pixels |
| ----- | --------- | ----------- | ---------- |
| 8GB+  | 50MB      | 20 images   | 8M pixels  |
| 4-8GB | 30MB      | 15 images   | 6M pixels  |
| 2-4GB | 20MB      | 10 images   | 4M pixels  |
| <2GB  | 10MB      | 5 images    | 2M pixels  |

### Supported Formats

- JPG, PNG, WebP, TIFF

## 🔧 Development

### Project Structure

```
rembg-api/
├── app.py                    # Main application
├── services/
│   └── rembg_service.py      # REMBG service logic
├── routes/
│   └── api.py               # API endpoints
├── requirements.txt
└── README.md
```

## 📄 License

This project is licensed under the MIT License.
