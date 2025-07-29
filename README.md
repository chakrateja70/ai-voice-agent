# AI Voice Calling Agent with Seamless M4T

A FastAPI-based AI voice calling agent that uses Twilio for voice calls, Google Gemini for conversation handling, and Meta's Seamless M4T v2 for advanced speech-to-text and text-to-speech processing.

## Features

- 🎙️ **Advanced STT/TTS**: Meta's Seamless M4T v2 for high-quality speech processing
- 🤖 **AI-powered conversations**: Google Gemini for intelligent responses  
- 📞 **Voice calling**: Twilio integration for phone calls
- 🌍 **Multilingual support**: Seamless M4T supports multiple languages
- 📊 **Call logging**: Database integration for call history and transcripts
- ⚡ **Real-time processing**: WebSocket support for live audio streaming
- 🔧 **GPU acceleration**: CUDA support for faster processing

## Prerequisites

- Python 3.8+
- Twilio account with phone number
- Google AI API key
- MySQL database (optional)
- **GPU recommended**: NVIDIA GPU with CUDA support for optimal performance
- **RAM**: At least 8GB RAM (16GB recommended for GPU usage)
- **Storage**: ~5GB for model files

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   Or run the automated setup:
   ```bash
   python setup.py
   ```

2. **Environment variables**
   Create a `.env` file in the root directory:
   ```env
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   GEMINI_API_KEY=your_google_ai_api_key
   WEBHOOK_BASE_URL=your_ngrok_or_server_url
   
   # Database (optional)
   DATABASE_URL=mysql+aiomysql://user:password@localhost/dbname
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

   The API will be available at `http://localhost:8000`

## Seamless M4T Integration

This application now uses Meta's Seamless M4T v2 model for:

### Speech-to-Text (STT)
- High-quality transcription in multiple languages
- Real-time processing capability
- Better accuracy than traditional ASR systems

### Text-to-Speech (TTS)  
- Natural-sounding voice synthesis
- Multilingual voice generation
- Consistent voice quality

### Configuration
Seamless M4T settings can be configured in `app/config/seamless_config.py`:

```python
# Model settings
SEAMLESS_MODEL_NAME = "facebook/seamless-m4t-v2-large"
SEAMLESS_DEVICE = "cuda"  # or "cpu"

# Audio settings
AUDIO_SAMPLE_RATE = 16000
DEFAULT_SRC_LANG = "eng"  # English
DEFAULT_TGT_LANG = "eng"  # English
```

## API Endpoints

- `POST /outgoing-call` - Initiate an outgoing call
- `POST /call-webhook/{call_log_id}` - Twilio voice webhook handler
- `POST /call-response/{call_log_id}` - Handle call responses
- `WS /ws/audio/{call_log_id}` - WebSocket for real-time audio streaming
- `POST /media-webhook/{call_log_id}` - Handle Twilio media streams

## Usage

To make an outgoing call:
```bash
curl -X POST "http://localhost:8000/outgoing-call" \
     -H "Content-Type: application/json" \
     -d '{
       "phone_number": "+1234567890",
       "conversation_type": "customer_feedback",
       "greeting": "Hello! This is an AI assistant calling for feedback."
     }'
```

## Performance Notes

### GPU Usage
- **Recommended**: NVIDIA GPU with 8GB+ VRAM
- **Minimum**: 4GB VRAM for basic functionality
- CPU-only mode available but significantly slower

### Model Loading
- First startup may take 2-5 minutes to download model files (~5GB)
- Subsequent startups are faster as models are cached locally
- Models are stored in `~/.cache/huggingface/transformers/`

### Audio Processing
- Real-time STT processing: ~100-500ms latency
- TTS generation: ~200-1000ms depending on text length
- WebSocket streaming for minimal latency

## Troubleshooting

### CUDA Issues
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# If CUDA is not available, the system will fall back to CPU
```

### Memory Issues
- Reduce model size by using `facebook/seamless-m4t-medium` instead
- Close other applications to free up RAM/VRAM
- Use CPU mode if GPU memory is insufficient

### Audio Quality
- Ensure audio sample rate is 16kHz for best results
- Use high-quality microphones for better STT accuracy
- Check network connectivity for real-time processing

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Twilio Call   │    │   FastAPI App    │    │  Seamless M4T   │
│                 │◄──►│                  │◄──►│                 │
│  - Voice Input  │    │  - Conversation  │    │  - STT/TTS      │
│  - Audio Output │    │  - WebSockets    │    │  - Multilingual │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Google Gemini   │
                       │                   │
                       │  - LLM Processing │
                       │  - Conversation   │
                       └──────────────────┘
```