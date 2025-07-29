import os
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from dotenv import load_dotenv

from app.db.database import get_db
from app.models.schemas import OutgoingCallRequest
from app.services.conversation_service import ConversationService

load_dotenv()

router = APIRouter()

@router.get("/")
def read_root():
    return {"message": "Welcome to the Voice Calling Agent API!"}

@router.get("/test-webhook/{call_log_id}")
async def test_webhook(call_log_id: int):
    """Test endpoint to verify webhook URL is working"""
    return {
        "status": "success",
        "message": f"Webhook test successful for call_log_id: {call_log_id}",
        "webhook_url": f"{os.getenv('WEBHOOK_BASE_URL')}/call-webhook/{call_log_id}"
    }

@router.post("/outgoing-call")
async def create_outgoing_call(
    request: OutgoingCallRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Initiate an outgoing call with specified parameters
    
    Request body should contain:
    - phone_number: The phone number to call
    - conversation_type: Type of conversation (customer_feedback, sales_inquiry, etc.)
    - greeting: Initial greeting message
    """
    try:
        # Initialize conversation service
        conversation_service = ConversationService(db)
        
        # Get webhook base URL from environment variables
        webhook_base_url = os.getenv('WEBHOOK_BASE_URL')
        if not webhook_base_url:
            raise HTTPException(status_code=500, detail="WEBHOOK_BASE_URL not configured in environment variables")
        
        # Remove trailing slash if present
        webhook_base_url = webhook_base_url.rstrip('/')
        
        # Initiate the call
        result = await conversation_service.initiate_outgoing_call(request, webhook_base_url)
        
        if result["success"]:
            return {
                "status": "success",
                "message": "Call initiated successfully",
                "call_log_id": result["call_log_id"],
                "call_sid": result["call_sid"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/call-webhook/{call_log_id}")
async def handle_call_webhook(
    call_log_id: int,
    request: Request,
    call_sid: str = Form(default=None, alias="CallSid"),
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook endpoint for Twilio to handle incoming call events
    """
    try:
        # Log all incoming data for debugging
        form_data = await request.form()
        print(f"🔔 Webhook called for call_log_id: {call_log_id}")
        print(f"   Call SID: {call_sid}")
        print(f"   Form data: {dict(form_data)}")
        
        conversation_service = ConversationService(db)
        twiml_response = await conversation_service.handle_call_webhook(call_log_id, call_sid)
        
        print(f"📤 Sending TwiML response: {twiml_response[:200]}...")
        
        # Add headers to bypass ngrok browser warning
        headers = {
            "ngrok-skip-browser-warning": "true",
            "Content-Type": "application/xml"
        }
        
        return Response(content=twiml_response, media_type="application/xml", headers=headers)
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        
        error_twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">Sorry, an error occurred. Goodbye!</Say>
    <Hangup/>
</Response>"""
        return Response(content=error_twiml, media_type="application/xml")

@router.post("/call-response/{call_log_id}")
async def handle_call_response(
    call_log_id: int,
    request: Request,
    speech_result: str = Form(alias="SpeechResult"),
    call_sid: str = Form(alias="CallSid"),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle user's speech response during the call
    """
    try:
        print(f"🎤 User response received for call {call_log_id}")
        print(f"   Speech Result: {speech_result}")
        print(f"   Call SID: {call_sid}")
        
        conversation_service = ConversationService(db)
        twiml_response = await conversation_service.handle_user_response(
            call_log_id, speech_result, call_sid
        )
        
        print(f"📤 Sending user response TwiML: {twiml_response[:200]}...")
        
        # Add headers to bypass ngrok browser warning
        headers = {
            "ngrok-skip-browser-warning": "true",
            "Content-Type": "application/xml"
        }
        
        return Response(content=twiml_response, media_type="application/xml", headers=headers)
        
    except Exception as e:
        print(f"❌ Call response error: {e}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        
        error_twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">Sorry, I didn't understand. Goodbye!</Say>
    <Hangup/>
</Response>"""
        return Response(content=error_twiml, media_type="application/xml")

@router.get("/call-transcript/{call_log_id}")
async def get_call_transcript(
    call_log_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the complete transcript and analysis of a call
    """
    try:
        conversation_service = ConversationService(db)
        transcript = await conversation_service.get_call_transcript(call_log_id)
        
        if "error" in transcript:
            raise HTTPException(status_code=404, detail=transcript["error"])
        
        return transcript
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/recent-calls")
async def get_recent_calls(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent call logs
    """
    try:
        from app.services.call_log_service import CallLogService
        
        call_log_service = CallLogService(db)
        calls = await call_log_service.get_recent_calls(limit)
        
        return {
            "calls": [
                {
                    "id": call.id,
                    "phone_number": call.phone_number,
                    "conversation_type": call.conversation_type.value,
                    "status": call.status.value,
                    "created_at": call.created_at.isoformat(),
                    "duration_seconds": call.duration_seconds
                }
                for call in calls
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
