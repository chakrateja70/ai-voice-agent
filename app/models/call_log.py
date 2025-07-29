import enum

from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.sql import func

from app.db.database import Base

class ConversationType(enum.Enum):
    customer_feedback = "customer_feedback"
    sales_inquiry = "sales_inquiry"
    appointment_reminder = "appointment_reminder"
    survey = "survey"
    support = "support"
    general = "general"

class CallStatus(enum.Enum):
    initiated = "initiated"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"
    no_answer = "no_answer"

class CallLog(Base):
    __tablename__ = "call_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), nullable=False)
    conversation_type = Column(Enum(ConversationType), nullable=False)
    greeting = Column(Text, nullable=False)
    status = Column(Enum(CallStatus), default=CallStatus.initiated)
    call_sid = Column(String(100), nullable=True)  # Twilio call SID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
class ConversationTranscript(Base):
    __tablename__ = "conversation_transcripts"
    
    id = Column(Integer, primary_key=True, index=True)
    call_log_id = Column(Integer, nullable=False)  # Foreign key to call_logs
    speaker = Column(Enum('bot', 'user', name='speaker_enum'), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    intent_detected = Column(String(100), nullable=True)  # For user messages
    confidence_score = Column(String(10), nullable=True)  # For intent detection
