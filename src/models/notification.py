from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class Notification(BaseModel):
    id: UUID
    receiver_id: UUID
    sender_id: UUID
    visionboard_id: UUID
    genre_id: Optional[UUID]
    assignment_id: Optional[UUID]
    type: str
    status: str
    message: Optional[str]
    created_at: datetime
    updated_at: datetime
    response: Optional[str]
    comment: Optional[str] 