# AI Voice Calling Agent

## 1. Project Overview

This project is all about building a smart voice-calling system that can make calls automatically and talk to people just like a human would. It uses Twilio to handle phone calls and Google Gemini (a powerful AI model) to understand and respond to conversations.

The system can call users, have a back-and-forth conversation with them, and then save the details of the call—including what was said—into a MySQL database. It’s useful for things like:

- Collecting customer feedback  
- Conducting automated interviews  
- Sending appointment reminders  
- Running surveys  
- Offering basic support over the phone  

## 2. Architecture

- **FastAPI**: Serves as the web framework for API endpoints.
- **Twilio**: Handles telephony (outgoing calls, speech-to-text, text-to-speech).
- **Google Gemini LLM**: Provides conversational intelligence for dynamic, context-aware responses.
- **MySQL**: Stores call logs and conversation transcripts.
- **SQLAlchemy (Async)**: ORM for database operations.
- **ngrok**: Used for exposing local server to the internet for Twilio webhooks during development.

### High-Level Flow

1. **API Request**: Client requests an outgoing call via `/outgoing-call` endpoint.
2. **Call Initiation**: The backend uses Twilio to place the call and sets up webhooks for call events.
3. **Conversation**: User interacts with the AI agent (powered by Gemini LLM) via phone. The agent responds contextually.
4. **Logging**: All call details and conversation messages are logged in the database.
5. **Completion**: The call ends based on user input or conversation logic, and the status is updated.

## 3. Setup and Installation

### Prerequisites
- Python 3.8+
- MySQL database
- Twilio account (for telephony)
- Google Gemini API key
- ngrok (for local development)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/chakrateja70/ai-voice-agent.git
   cd ai-voice-agent
   ```
2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure environment variables**
   - Create a `.env` file in the project root (see below for required variables).
5. **Set up the MySQL database**
   - Create a database and user matching your `.env` settings.
   - Run the provided `setup_db.sql` script in your MySQL client (replace placeholders with your actual `.env` values):
     ```bash
     mysql -u root -p < setup_db.sql
     ```
   - This will create the database and user. Tables will be created automatically on first run by SQLAlchemy.
6. **Run the application**
   ```bash
   uvicorn main:app --reload
   ```
7. **Expose your local server to the internet (for Twilio webhooks)**
   ```bash
   ./ngrok http 8000
   ```
   - After running this command, ngrok will provide a public URL (e.g., `https://xxxx-xxxx-xxxx.ngrok-free.app`).
   - Copy this URL and update the `WEBHOOK_BASE_URL` variable in your `.env` file:
     ```ini
     WEBHOOK_BASE_URL=https://xxxx-xxxx-xxxx.ngrok-free.app
     ```
   - Also, use this URL as the base for your webhook endpoints in the Twilio Console (under Voice > Webhooks) to ensure Twilio can reach your local FastAPI server.

## 4. .env Configuration

Create a `.env` file in the project root with the following variables:

```env
MYSQL_USER=username
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=ai_voice_calling_agent

GEMINI_API_KEY=your_gemini_api_key

TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number

WEBHOOK_BASE_URL=https://your-ngrok-url.ngrok-free.app
```

## Logging

Logs are saved to the `logs/ai_voice_agent.log` file and also output to the console.

