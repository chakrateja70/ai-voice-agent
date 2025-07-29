import logging
import os
import traceback
from dotenv import load_dotenv

from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.twilio_service import TwilioService
from app.services.llm_service import LLMService
from app.services.call_log_service import CallLogService
from app.models.schemas import OutgoingCallRequest
from app.models.call_log import CallStatus

load_dotenv()

# Use existing logger instead of configuring again
logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.twilio_service = TwilioService()
        self.llm_service = LLMService()
        self.call_log_service = CallLogService(db)
        
        # Store active conversations and webhook base URL
        self.active_conversations: Dict[str, Dict[str, Any]] = {}
        self.webhook_base_url = os.getenv('WEBHOOK_BASE_URL', 'https://your-ngrok-url.ngrok-free.app')
    
    async def initiate_outgoing_call(self, request: OutgoingCallRequest, webhook_base_url: str) -> Dict[str, Any]:
        """
        Initiate an outgoing call with the provided parameters
        
        Args:
            request: Call request parameters
            webhook_base_url: Base URL for webhooks
            
        Returns:
            Dictionary with call status and details
        """
        try:
            # Store webhook base URL for later use
            self.webhook_base_url = webhook_base_url
            
            # Create call log
            call_log = await self.call_log_service.create_call_log(request)
            
            # Generate webhook URL for this specific call with ngrok bypass
            webhook_url = f"{webhook_base_url}/call-webhook/{call_log.id}?ngrok-skip-browser-warning=true"
            
            # Make the call using Twilio
            call_sid = self.twilio_service.make_outgoing_call(
                to_number=request.phone_number,
                webhook_url=webhook_url
            )
            
            if call_sid:
                # Update call log with SID
                await self.call_log_service.update_call_status(
                    call_log.id, CallStatus.in_progress, call_sid
                )
                
                # Store conversation context
                self.active_conversations[call_sid] = {
                    "call_log_id": call_log.id,
                    "conversation_type": request.conversation_type,
                    "greeting": request.greeting,
                    "turn_count": 0,
                    "conversation_history": []
                }
                
                logger.info(f"Call initiated successfully. Call ID: {call_log.id}, SID: {call_sid}")
                return {
                    "success": True,
                    "call_log_id": call_log.id,
                    "call_sid": call_sid,
                    "message": "Call initiated successfully"
                }
            else:
                # Update status to failed
                await self.call_log_service.update_call_status(call_log.id, CallStatus.failed)
                return {
                    "success": False,
                    "call_log_id": call_log.id,
                    "message": "Failed to initiate call"
                }
                
        except Exception as e:
            logger.error(f"Failed to initiate outgoing call: {str(e)}")
            return {
                "success": False,
                "message": f"Error initiating call: {str(e)}"
            }
    
    async def handle_call_webhook(self, call_log_id: int, call_sid: str = None) -> str:
        """
        Generate TwiML response for call webhook with simpler approach
        
        Args:
            call_log_id: ID of the call log
            
        Returns:
            TwiML response string
        """
        try:
            # Get call details
            call_log = await self.call_log_service.get_call_log(call_log_id)
            if not call_log:
                return self._generate_error_twiml("Call not found")
            
            # Initialize conversation state with real call_sid if available, otherwise use temp key
            conversation_key = call_sid if call_sid else f"call_{call_log_id}"
            
            # Initialize conversation state
            self.active_conversations[conversation_key] = {
                "turn_count": 0,
                "conversation_history": [],
                "conversation_type": call_log.conversation_type.value,
                "call_log_id": call_log_id
            }
            
            logger.info(f"Initialized conversation for call {call_log_id}")
            
            # Use simple TwiML instead of media streaming for now
            logger.info(f"Generating simple TwiML for call {call_log_id}")
            logger.info(f"Greeting: {call_log.greeting}")
            
            # Create simple TwiML response that works reliably
            twiml_response = self._generate_continue_twiml(call_log.greeting, call_log_id)
            
            # Log the bot's greeting
            await self.call_log_service.add_conversation_message(
                call_log_id, "bot", call_log.greeting
            )
            
            return twiml_response
            
        except Exception as e:
            logger.error(f"Error handling call webhook: {str(e)}")
            return self._generate_error_twiml("Internal error occurred")
    
    async def handle_user_response(self, call_log_id: int, speech_result: str, call_sid: str) -> str:
        """
        Handle user's speech response and generate bot reply using Twilio STT/TTS
        
        Args:
            call_log_id: ID of the call log
            speech_result: Transcribed user speech from Twilio STT
            call_sid: Twilio call SID
            
        Returns:
            TwiML response string
        """
        try:
            conversation_key = call_sid
            conversation_context = self.active_conversations.get(conversation_key, {
                "turn_count": 0,
                "conversation_history": [],
                "conversation_type": "general"
            })
            
            turn_count = conversation_context.get("turn_count", 0)
            conversation_history = conversation_context.get("conversation_history", [])
            conversation_type = conversation_context.get("conversation_type", "general")
            
            logger.info(f"Processing user response: turn={turn_count}, user='{speech_result}'")
            
            # Check for conversation ending keywords
            ending_keywords = ["bye", "goodbye", "thank you", "thanks", "see you", "talk to you later", "ttyl", "end", "stop", "no", "nothing", "nope", "that's all", "all good", "no thanks", "i'm good"]
            user_message_lower = speech_result.lower().strip()
            
            # Check if user wants to end conversation
            should_end_conversation = (
                any(keyword in user_message_lower for keyword in ending_keywords) or
                (turn_count >= 2 and user_message_lower in ["no", "nope", "nothing"])  # End after 2 turns if user says no
            )
            
            # Log user response
            await self.call_log_service.add_conversation_message(
                call_log_id, "user", speech_result
            )
            
            if should_end_conversation:
                logger.info(f"Ending conversation - detected ending keywords in: '{speech_result}'")
                
                # Log final bot response
                final_response = "Thank you, have a good day!"
                await self.call_log_service.add_conversation_message(
                    call_log_id, "bot", final_response
                )
                
                # Mark call as completed and clean up
                await self.call_log_service.update_call_status(call_log_id, CallStatus.completed)
                if conversation_key in self.active_conversations:
                    del self.active_conversations[conversation_key]
                
                return self._generate_hangup_twiml(final_response)
            
            # Generate response using LLM
            bot_response_data = self.llm_service.generate_optimized_bot_response(
                conversation_type, speech_result, conversation_history, turn_count
            )
            
            bot_response = bot_response_data.get("response", "I understand. Thank you for sharing that with me.")
            intent = bot_response_data.get("intent", "neutral")
            confidence = bot_response_data.get("confidence", "medium")
            
            # Log bot response with intent and confidence
            await self.call_log_service.add_conversation_message(
                call_log_id, "bot", bot_response, intent, confidence
            )
            
            # Update conversation history
            conversation_history.append({
                "speaker": "user",
                "message": speech_result,
                "intent": intent
            })
            
            conversation_history.append({
                "speaker": "bot", 
                "message": bot_response
            })
            
            turn_count += 1
            
            # Update active conversation with proper key
            self.active_conversations[conversation_key] = {
                "turn_count": turn_count,
                "conversation_history": conversation_history,
                "conversation_type": conversation_type,
                "call_log_id": call_log_id
            }
            
            # End conversation after 2 turns or if user clearly wants to end
            should_end_by_turns = (
                turn_count >= 2 or  # End after 2 exchanges
                bot_response_data.get("should_continue", True) == False or  # LLM says should end
                bot_response_data.get("intent") == "wants_to_end"  # User wants to end
            )
            
            if should_end_by_turns:
                logger.info(f"Ending conversation: turns={turn_count}, should_continue={bot_response_data.get('should_continue')}")
                
                # Use a more natural ending response
                if "no" in speech_result.lower() or "nothing" in speech_result.lower():
                    ending_response = "Understood. Thank you for your time. Have a great day!"
                else:
                    ending_response = f"{bot_response} Thank you for your time. Have a great day!"
                
                # Mark call as completed and clean up
                await self.call_log_service.update_call_status(call_log_id, CallStatus.completed)
                if conversation_key in self.active_conversations:
                    del self.active_conversations[conversation_key]
                
                twiml_response = self._generate_hangup_twiml(ending_response)
            else:
                # Continue conversation
                twiml_response = self._generate_continue_twiml(bot_response, call_log_id)
            
            return twiml_response
            
        except Exception as e:
            logger.error(f"Error handling user response: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return self._generate_error_twiml("Sorry, I encountered an error")
    
    def _generate_error_twiml(self, message: str) -> str:
        """Generate error TwiML response"""
        # Escape any XML special characters in the message
        escaped_message = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&apos;").replace('"', "&quot;")
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">{escaped_message}. Goodbye!</Say>
    <Hangup/>
</Response>"""

    def _generate_hangup_twiml(self, message: str) -> str:
        """Generate TwiML response that says a message and hangs up"""
        # Escape any XML special characters in the message
        escaped_message = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&apos;").replace('"', "&quot;")
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">{escaped_message}</Say>
    <Hangup/>
</Response>"""

    def _generate_continue_twiml(self, message: str, call_log_id: int) -> str:
        """
        Generate TwiML response that says a message and continues conversation using Twilio TTS
        
        Args:
            message: Message to speak
            call_log_id: ID of the call log
        """
        # Escape any XML special characters in the message
        escaped_message = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&apos;").replace('"', "&quot;")
        
        # Use Twilio's built-in TTS
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">{escaped_message}</Say>
    <Gather timeout="8" speechTimeout="2" input="speech" action="{self.webhook_base_url}/call-response/{call_log_id}?ngrok-skip-browser-warning=true" method="POST">
    </Gather>
    <Say voice="Polly.Joanna">Thank you for your time. Goodbye!</Say>
    <Hangup/>
</Response>"""
