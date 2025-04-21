from pydantic import BaseModel, EmailStr, UUID4
from datetime import datetime


# ==============================
# Auth Schemas
# ==============================


class User(BaseModel):
    id: UUID4
    email: str
    role: str

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ==============================
# Ticket Schemas
# ==============================

class TicketCreate(BaseModel):
    subject: str
    description: str


class Ticket(BaseModel):
    id: UUID4
    user_id: UUID4
    status: str
    title: str
    description: str
    messages: str

    created_at: datetime

    class Config:
        orm_mode = True

# ==============================
# Message Schemas
# ==============================

class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    ticket_id: int
    sender: str
    content: str
    timestamp: datetime

    class Config:
        orm_mode = True
