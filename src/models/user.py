from __future__ import annotations
import datetime

from pydantic import BaseModel, Field
import uuid
from typing import Optional, List
from src.models import UserGenre, WorkMode, PaymentMode

class UserModel(BaseModel):
    id: uuid.UUID = Field(default_factory=lambda: uuid.uuid4())

    name: str
    email: str
    password: str

    profile_image_url: Optional[str] = None
    age: Optional[int] = None
    genres: Optional[List[UserGenre]] = None
    payment_mode: Optional[PaymentMode] = None
    work_mode: Optional[WorkMode] = None
    


class ShowcaseModel(BaseModel):
    id: uuid.UUID = Field(default_factory=lambda: uuid.uuid4())
    owner_id: uuid.UUID
    visionboard: Optional[uuid.UUID]
    description: Optional[str] = None
    media_link: Optional[str] = None
    media_type: Optional[str] = None


class ShowCaseLikeModel(BaseModel):
    user_id: uuid.UUID
    showcase_id: uuid.UUID


class ShowCaseBookmarkModel(BaseModel):
    user_id: uuid.UUID
    showcase_id: uuid.UUID


class CommentModel(BaseModel):
    id: uuid.UUID
    showcase_id: uuid.UUID
    text: str
    author_id: uuid.UUID
    timestamp: datetime.datetime


class CommentUpvoteModel(BaseModel):
    user_id: uuid.UUID
    comment_id: uuid.UUID

class VisionBoardModel(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    description: str
    start_date: datetime.datetime
    end_date: datetime.datetime


class VisionBoardRoleModel(BaseModel):
    visionboard_id: uuid.UUID
    role: UserGenre
    user_id: uuid.UUID


class VisionBoardTaskModel(BaseModel):
    user_id: uuid.UUID
    visionboard_id: uuid.UUID
    title: str
    start_date: datetime.datetime
    end_date: datetime.datetime


class FollowerModel(BaseModel):
    user_id: uuid.UUID
    following_id: uuid.UUID
