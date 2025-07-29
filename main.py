import logging
import os
import sys

import uvicorn
from fastapi import FastAPI

from app.api import routes

# Ensure logs directory exists and configure logging properly
os.makedirs('logs', exist_ok=True)
log_file_path = os.path.join(os.getcwd(), 'logs', 'ai_voice_agent.log')

# Clear any existing handlers to avoid conflicts
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Configure logging with proper file handling
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
    ],
    force=True  # Force reconfiguration
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Voice Calling Agent",
    description="AI Voice Agent using Twilio for speech processing",
    version="1.0.0"
)

app.include_router(routes.router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to AI Voice Calling Agent",
        "status": "running",
        "version": "1.0.0"
    }

@app.on_event("startup")
async def startup_event():
    logger.info("AI Voice Calling Agent started")
    logger.info(f"Logs will be saved to: {log_file_path}")
    logger.info("Using Twilio STT/TTS for reliable voice processing")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "AI Voice Calling Agent is running with Twilio STT/TTS",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    logger.info("Starting development server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
