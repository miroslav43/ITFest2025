from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime

# Auth models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# User models
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: str = "user"  # Default role is "user", can be "admin"

class User(UserBase):
    id: str
    role: str
    created_at: datetime

class UserInDB(User):
    hashed_password: str

# Feedback models
class Feedback(BaseModel):
    rating: Optional[int] = None
    comment: str = ""

# Message models
class Message(BaseModel):
    id: str
    role: str
    content: str
    feedback: Optional[Feedback] = None

# Conversation models
class Conversation(BaseModel):
    id: str
    title: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime
    user_id: str

class ConversationCreate(BaseModel):
    title: str = "New Conversation"
    messages: List[Message] = []

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    messages: Optional[List[Message]] = None

# Chat models
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    conversation_id: str

# Feedback models
class FeedbackRequest(BaseModel):
    message_id: str
    conversation_id: str
    rating: int = Field(..., ge=1, le=10)
    comment: str = ""

# Admin models
class UserStats(BaseModel):
    user_id: str
    username: str
    conversation_count: int
    message_count: int
    average_rating: Optional[float] = None

class FeedbackStats(BaseModel):
    total_feedback_count: int
    average_rating: float
    rating_distribution: dict  # e.g., {1: 5, 2: 10, ...} meaning 5 ratings of 1, 10 ratings of 2, etc.