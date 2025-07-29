# AI Voice Calling Agent

## 1. Project Overview

AI Voice Calling Agent is a FastAPI-based backend application that enables automated voice calls using Twilio for telephony and Google Gemini LLM for conversational AI. The system can initiate outgoing calls, conduct interactive conversations with users, and log call details and transcripts in a MySQL database. It is designed for use cases such as customer feedback, sales inquiries, appointment reminders, surveys, and general support.

## 2. Problem Statement

Businesses often need to automate outbound voice calls for surveys, feedback, reminders, or sales, but traditional IVR systems are rigid and lack conversational intelligence. This project solves that by combining Twilio's reliable telephony with a powerful LLM (Google Gemini) to create a flexible, natural, and context-aware voice agent that can handle real conversations, log interactions, and adapt to various business needs.

## 3. Architecture

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

## 4. Setup and Installation

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
   - Run migrations or let SQLAlchemy create tables on first run.
6. **Run the application**
   ```bash
   uvicorn main:app --reload
   ```
7. **Expose your local server to the internet (for Twilio webhooks)**
   ```bash
   ./ngrok http 8000
   ```

## 5. .env Configuration

Create a `.env` file in the project root with the following variables:

```ini
# Twilio Credentials
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key

# MySQL Database
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=ai_voice_agent

# Webhook Base URL (e.g., your ngrok URL, no trailing slash)
WEBHOOK_BASE_URL=https://your-ngrok-url.ngrok-free.app
```

## Logging

Logs are saved to the `logs/ai_voice_agent.log` file and also output to the console.

## License

MIT (or specify your license) 