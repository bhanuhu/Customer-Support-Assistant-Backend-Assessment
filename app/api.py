from . import schemas, models
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status, APIRouter, Response
from sqlalchemy.exc import IntegrityError
from .database import get_db

router = APIRouter()

######

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@router.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]

######

@router.get('/')
def get_notes(db: Session = Depends(get_db), limit: int = 10, page: int = 1, search: str = ''):
    skip = (page - 1) * limit

    notes = db.query(models.Note).filter(
        models.Note.title.contains(search)).limit(limit).offset(skip).all()
    return {'status': 'success', 'results': len(notes), 'notes': notes}


@router.post('/', status_code=status.HTTP_201_CREATED)
def create_note(payload: schemas.NoteBaseSchema, db: Session = Depends(get_db)):
    new_note = models.Note(
        title=payload.title,
        content=payload.content,
        category=payload.category,
        published=payload.published
    )

    db.add(new_note)
    try:
        db.commit()
        db.refresh(new_note)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Note with this title already exists.")
    
    return {"status": "success", "note": new_note}


@router.patch('/{noteId}')
def update_note(noteId: str, payload: schemas.NotePatchSchema, db: Session = Depends(get_db)):
    note_query = db.query(models.Note).filter(models.Note.id == noteId)
    db_note = note_query.first()

    if not db_note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No note with this id: {noteId} found')

    update_data = payload.model_dump(exclude_unset=True)

    if 'title' in update_data:
        existing_title = db.query(models.Note).filter(
            models.Note.title == update_data['title'],
            models.Note.id != noteId  
        ).first()
        if existing_title:
            raise HTTPException(status_code=400, detail="Another note with this title already exists.")

    note_query.update(update_data, synchronize_session=False)
    db.commit()
    db.refresh(db_note)
    return {"status": "success", "note": db_note}


@router.get('/{noteId}')
def get_note(noteId: str, db: Session = Depends(get_db)):
    note = db.query(models.Note).filter(models.Note.id == noteId).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No note with this id: {noteId} found")
    return {"status": "success", "note": note}


@router.delete('/{noteId}')
def delete_note(noteId: str, db: Session = Depends(get_db)):
    note_query = db.query(models.Note).filter(models.Note.id == noteId)
    note = note_query.first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No note with this id: {noteId} found')
    note_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)