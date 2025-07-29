import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.call_log import CallLog, ConversationTranscript, CallStatus, ConversationType
from app.models.schemas import OutgoingCallRequest, CallLogResponse

# Use existing logger instead of configuring again
logger = logging.getLogger(__name__)

class CallLogService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_call_log(self, request: OutgoingCallRequest) -> CallLog:
        """Create a new call log entry"""
        try:
            call_log = CallLog(
                phone_number=request.phone_number,
                conversation_type=ConversationType(request.conversation_type),
                greeting=request.greeting,
                status=CallStatus.initiated
            )
            
            self.db.add(call_log)
            await self.db.commit()
            await self.db.refresh(call_log)
            
            logger.info(f"Call log created with ID: {call_log.id}")
            return call_log
            
        except Exception as e:
            logger.error(f"Failed to create call log: {str(e)}")
            await self.db.rollback()
            raise
    
    async def update_call_status(self, call_log_id: int, status: CallStatus, call_sid: str = None) -> bool:
        """Update call status and optionally set call SID"""
        try:
            query = select(CallLog).where(CallLog.id == call_log_id)
            result = await self.db.execute(query)
            call_log = result.scalar_one_or_none()
            
            if not call_log:
                logger.error(f"Call log not found with ID: {call_log_id}")
                return False
            
            call_log.status = status
            if call_sid:
                call_log.call_sid = call_sid
            
            if status == CallStatus.in_progress:
                call_log.started_at = datetime.utcnow()
            elif status in [CallStatus.completed, CallStatus.failed, CallStatus.no_answer]:
                call_log.ended_at = datetime.utcnow()
                if call_log.started_at:
                    duration = (call_log.ended_at - call_log.started_at).total_seconds()
                    call_log.duration_seconds = int(duration)
            
            await self.db.commit()
            logger.info(f"Call log {call_log_id} status updated to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update call status: {str(e)}")
            await self.db.rollback()
            return False
    
    async def add_conversation_message(self, call_log_id: int, speaker: str, message: str, 
                                     intent_detected: str = None, 
                                     confidence_score: str = None) -> bool:
        """Add a conversation message to the transcript"""
        try:
            logger.info(f"Saving message: call_id={call_log_id}, speaker={speaker}, message='{message[:50]}...', intent={intent_detected}")
            
            transcript = ConversationTranscript(
                call_log_id=call_log_id,
                speaker=speaker,
                message=message,
                intent_detected=intent_detected,
                confidence_score=confidence_score
            )
            
            self.db.add(transcript)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save conversation message for call {call_log_id}: {str(e)}")
            await self.db.rollback()
            return False
    
    async def get_call_log(self, call_log_id: int) -> Optional[CallLog]:
        """Get call log by ID"""
        try:
            query = select(CallLog).where(CallLog.id == call_log_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get call log: {str(e)}")
            return None
    
    async def get_call_transcripts(self, call_log_id: int) -> List[ConversationTranscript]:
        """Get all conversation transcripts for a call"""
        try:
            query = select(ConversationTranscript).where(
                ConversationTranscript.call_log_id == call_log_id
            ).order_by(ConversationTranscript.timestamp)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get call transcripts: {str(e)}")
            return []
