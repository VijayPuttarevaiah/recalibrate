from pydantic import BaseModel, ConfigDict
from datetime import datetime


class NotificationBase(BaseModel):
    title: str
    message: str


class NotificationResponse(NotificationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    is_read: bool
    created_at: datetime