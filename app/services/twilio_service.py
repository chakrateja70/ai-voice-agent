import logging
import os
from typing import Optional

from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

# Use existing logger instead of configuring again
logger = logging.getLogger(__name__)

class TwilioService:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        if not all([self.account_sid, self.auth_token, self.phone_number]):
            raise ValueError("Missing Twilio credentials in environment variables")
        
        self.client = Client(self.account_sid, self.auth_token)
    
    def make_outgoing_call(self, to_number: str, webhook_url: str) -> Optional[str]:
        """
        Make an outgoing call using Twilio
        Returns the call SID if successful, None if failed
        """
        try:
            logger.info(f"Initiating Twilio call to {to_number}")
            
            # Create call parameters
            call_params = {
                'url': webhook_url,
                'to': to_number,
                'from_': self.phone_number,
                'timeout': 30,  # Ring for 30 seconds before timing out
                'record': False  # Disable call recording
            }
            
            call = self.client.calls.create(**call_params)
            
            logger.info(f"Call initiated successfully: SID={call.sid}, status={call.status}")
            return call.sid
        except Exception as e:
            logger.error(f"Failed to make call to {to_number}: {str(e)}")
            return None
    
    def get_call_status(self, call_sid: str) -> Optional[str]:
        """Get the current status of a call"""
        try:
            call = self.client.calls(call_sid).fetch()
            return call.status
        except Exception as e:
            logger.error(f"Failed to get call status for {call_sid}: {str(e)}")
            return None
    
    def hang_up_call(self, call_sid: str) -> bool:
        """Hang up an active call"""
        try:
            self.client.calls(call_sid).update(status='completed')
            logger.info(f"Call {call_sid} hung up successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to hang up call {call_sid}: {str(e)}")
            return False
