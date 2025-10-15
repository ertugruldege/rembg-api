# REMBG API

A high-quality REST API for background removal with multiple providers. Remove backgrounds from images at maximum quality using REMBG or Withoutbg AI models.

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/ertugruldege/rembg-api.git
cd rembg-api
pip install -r requirements.txt
python app.py
```

API will be available at `http://localhost:5000`

## ✨ Features

- 🎯 **Multiple Provider Support**: Choose between REMBG and Withoutbg
- 🤖 **Multiple AI Models**: 5 different AI model options
- 📦 **Batch Processing**: Unlimited batch processing support
- 💎 **Maximum Quality Output**: No compression, full quality preservation
- 🚀 **High Performance**: Fast processing with optimized AI models
- 📊 **Detailed Logging**: Comprehensive logging for every operation
- 🔄 **Flexible Format Support**: JPG, PNG, WebP, TIFF
- ⚡ **No Resolution Limits**: Process images at their original resolution

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
- image: Image file (required, max 40MB)
- provider: Service provider (optional, default: rembg) - Options: rembg, withoutbg
- model: AI model (optional, default: u2net) - Only for rembg provider
```

**Examples:**

```bash
# Using REMBG (default)
curl -X POST -F "image=@photo.jpg" http://localhost:5000/remove-bg

# Using REMBG with specific model
curl -X POST -F "image=@photo.jpg" -F "model=u2net_human_seg" http://localhost:5000/remove-bg

# Using Withoutbg
curl -X POST -F "image=@photo.jpg" -F "provider=withoutbg" http://localhost:5000/remove-bg
```

### Batch Processing

```http
POST /batch
Content-Type: multipart/form-data

Parameters:
- images: Multiple image files (required, each max 40MB)
- provider: Service provider (optional, default: rembg) - Options: rembg, withoutbg
- model: AI model (optional, default: u2net) - Only for rembg provider
```

**Example:**

```bash
curl -X POST \
  -F "images=@photo1.jpg" \
  -F "images=@photo2.jpg" \
  -F "provider=withoutbg" \
  http://localhost:5000/batch
```

### Get Models

```http
GET /models?provider=rembg
```

**Examples:**

```bash
# Get REMBG models
curl http://localhost:5000/models?provider=rembg

# Get Withoutbg models
curl http://localhost:5000/models?provider=withoutbg
```

### System Info

```http
GET /system
```

## 🤖 Providers & Models

### REMBG Provider (default)

| Model               | Description                   | Size  | Speed  | Quality   |
| ------------------- | ----------------------------- | ----- | ------ | --------- |
| `u2net`             | Standard model (best balance) | 176MB | Medium | High      |
| `silueta`           | Compact model (fast)          | 44MB  | Fast   | Good      |
| `u2net_human_seg`   | Specifically for humans       | 176MB | Medium | Excellent |
| `isnet-general-use` | Improved model (latest)       | 179MB | Medium | High      |

### Withoutbg Provider

| Model  | Description                      | Speed | Quality |
| ------ | -------------------------------- | ----- | ------- |
| `snap` | Open source Snap model (default) | Fast  | High    |

**Provider Features:**

- **REMBG**: Multiple model options, wide range of use cases, maximum quality output
- **Withoutbg**: Fast processing, AI-powered edge detection, local processing, maximum quality output

## ⚙️ Configuration

### Environment Variables

Copy `env.example` to `.env` and configure:

```bash
cp env.example .env
```

**Required:**

- `PORT`: Application port (default: 5000)
- `FLASK_ENV`: Flask environment (development/production)

### Supported Formats

- JPG, PNG, WebP, TIFF

### API Limits

- **Maximum File Size**: 40MB per image
- **Maximum Resolution**: Unlimited (processes at original resolution)
- **Batch Processing**: Unlimited number of images
- **Output Quality**: Maximum (no compression applied)

## 🔧 Development

### Project Structure

```
rembg-api/
├── app.py                       # Main application
├── services/
│   ├── rembg_service.py         # REMBG service logic
│   └── withoutbg_service.py     # Withoutbg service logic
├── routes/
│   └── api.py                   # API endpoints
├── requirements.txt
└── README.md
```

## 📄 License

This project is licensed under the MIT License.
