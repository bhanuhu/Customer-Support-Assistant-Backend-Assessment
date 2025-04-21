from datetime import datetime, timedelta, timezone
from typing import Optional, Annotated, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from groq import Groq

from . import models, schemas
from .database import get_db
from .config import settings

security = HTTPBearer()


# ----------------- CONFIGURATION ------------------
# Generate a secure random key, e.g., `openssl rand -hex 32`
SECRET_KEY = "YOUR_SECURE_RANDOM_SECRET_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
groq_client = Groq(api_key=settings.GROQ_API_KEY)

router = APIRouter()

# ----------------- UTILITIES ------------------

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_user(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def authenticate_user(db, email: str, password: str):
    user = get_user(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(sub: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {"sub": sub}
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ----------------- DEPENDENCIES ------------------
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    token = credentials.credentials
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    user = get_user(db, email)
    if user is None:
        raise credentials_exc

    return user


@router.post("/auth/signup", response_model=schemas.User)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = pwd_context.hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Login
@router.post("/auth/login", response_model=schemas.Token)
def login(form_data: schemas.UserLogin = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.email).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode(
        {"sub": user.email, "exp": datetime.utcnow() + access_token_expires},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return {"access_token": access_token, "token_type": "bearer"}

# List Tickets
@router.get("/tickets", response_model=List[schemas.Ticket])
def list_tickets(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Ticket).filter(models.Ticket.user_id == current_user.id).all()

# Create Ticket
@router.post("/tickets", response_model=schemas.Ticket)
def create_ticket(ticket: schemas.TicketCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_ticket = models.Ticket(**ticket.dict(), user_id=current_user.id)
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket

# Get Ticket Details
@router.get("/tickets/{ticket_id}", response_model=schemas.Ticket)
def get_ticket(ticket_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id, models.Ticket.user_id == current_user.id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

# Add Message to Ticket
@router.post("/tickets/{ticket_id}/messages", response_model=schemas.MessageResponse)
def add_message(ticket_id: int, message: schemas.MessageCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id, models.Ticket.user_id == current_user.id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    new_message = models.Message(**message.dict(), ticket_id=ticket_id, user_id=current_user.id)
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

# SSE AI Response
@router.get("/tickets/{ticket_id}/ai-response", response_model=schemas.MessageResponse)
async def ai_response(ticket_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id, models.Ticket.user_id == current_user.id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Prepare the conversation history
    messages = [{"role": "user", "content": msg.content} for msg in ticket.messages]

    # Generate the AI response using Groq
    response = groq_client.chat.completions.create(
        model="llama3-8b-8192",  # Replace with your desired model
        messages=messages,
        stream=True
    )

    # Stream the response back to the client
    async def event_generator():
        async for chunk in response:
            if chunk.choices:
                content = chunk.choices[0].delta.get("content", "")
                yield f"data: {content}\n\n"
            await asyncio.sleep(0.1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
