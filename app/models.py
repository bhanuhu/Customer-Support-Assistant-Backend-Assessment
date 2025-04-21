from .database import Base
import uuid
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import TIMESTAMP, Column, String, Boolean, UUID, ForeignKey, DateTime, Integer, Text
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")
    
    tickets = relationship("Ticket", back_populates="user")

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    title = Column(String)
    description = Column(String)
    status = Column(String, default="open")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user_id = Column(UUID, ForeignKey("users.id"))
    user = relationship("User", back_populates="tickets")
    messages = relationship("Message", back_populates="ticket")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    content = Column(String)
    is_ai = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    ticket_id = Column(UUID, ForeignKey("tickets.id"))
    ticket = relationship("Ticket", back_populates="messages")
