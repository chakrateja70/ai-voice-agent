from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

class ConversationType(str, Enum):
    customer_feedback = "customer_feedback"
    sales_inquiry = "sales_inquiry"
    appointment_reminder = "appointment_reminder"
    survey = "survey"
    support = "support"
    general = "general"

class CallStatus(str, Enum):
    initiated = "initiated"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"
    no_answer = "no_answer"

class OutgoingCallRequest(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=20, description="Phone number to call")
    conversation_type: ConversationType = Field(..., description="Type of conversation")
    greeting: str = Field(..., min_length=10, max_length=500, description="Initial greeting message")

class CallLogResponse(BaseModel):
    id: int
    phone_number: str
    conversation_type: ConversationType
    greeting: str
    status: CallStatus
    call_sid: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]

class ConversationMessage(BaseModel):
    speaker: str
    message: str
    timestamp: datetime
    intent_detected: Optional[str] = None
    confidence_score: Optional[str] = None
