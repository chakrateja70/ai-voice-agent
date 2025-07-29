import os
import logging
from dotenv import load_dotenv

from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.schemas import OutgoingCallRequest
from app.services.conversation_service import ConversationService

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter()

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
        logger.info(f"Outgoing call request: {request.phone_number}, type: {request.conversation_type}")
        
        # Initialize conversation service
        conversation_service = ConversationService(db)
        
        # Get webhook base URL from environment variables
        webhook_base_url = os.getenv('WEBHOOK_BASE_URL')
        if not webhook_base_url:
            logger.error("WEBHOOK_BASE_URL not configured")
            raise HTTPException(status_code=500, detail="WEBHOOK_BASE_URL not configured in environment variables")
        
        # Remove trailing slash if present
        webhook_base_url = webhook_base_url.rstrip('/')
        
        # Initiate the call
        result = await conversation_service.initiate_outgoing_call(request, webhook_base_url)
        
        if result["success"]:
            logger.info(f"Call initiated successfully: ID={result['call_log_id']}, SID={result['call_sid']}")
            return {
                "status": "success",
                "message": "Call initiated successfully",
                "call_log_id": result["call_log_id"],
                "call_sid": result["call_sid"]
            }
        else:
            logger.error(f"Call initiation failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        logger.error(f"Outgoing call error: {str(e)}")
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
        logger.info(f"Webhook received: call_log_id={call_log_id}, call_sid={call_sid}")
        
        conversation_service = ConversationService(db)
        twiml_response = await conversation_service.handle_call_webhook(call_log_id, call_sid)
        
        # Add headers to bypass ngrok browser warning
        headers = {
            "ngrok-skip-browser-warning": "true",
            "Content-Type": "application/xml"
        }
        
        return Response(content=twiml_response, media_type="application/xml", headers=headers)
        
    except Exception as e:
        logger.error(f"Webhook error for call {call_log_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        error_twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Sorry, an error occurred. Goodbye!</Say>
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
        logger.info(f"User speech received: call_id={call_log_id}, text='{speech_result}'")
        
        conversation_service = ConversationService(db)
        twiml_response = await conversation_service.handle_user_response(
            call_log_id, speech_result, call_sid
        )
        
        # Add headers to bypass ngrok browser warning
        headers = {
            "ngrok-skip-browser-warning": "true",
            "Content-Type": "application/xml"
        }
        
        return Response(content=twiml_response, media_type="application/xml", headers=headers)
        
    except Exception as e:
        logger.error(f"Call response error for call {call_log_id}: {e}")
        
        error_twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Sorry, I didn't understand. Goodbye!</Say>
    <Hangup/>
</Response>"""
        return Response(content=error_twiml, media_type="application/xml")