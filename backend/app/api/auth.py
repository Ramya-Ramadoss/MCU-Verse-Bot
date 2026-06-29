import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.core.security import create_access_token, get_password_hash, verify_password
from backend.app.db.models.user import Settings, User
from backend.app.models.auth import TokenResponse, UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_for_user(user: User) -> TokenResponse:
    return TokenResponse(access_token=create_access_token(user.id), user=UserResponse.model_validate(user))


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email is already registered")

    is_first_user = db.query(User).count() == 0
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role="admin" if is_first_user else "user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    db.add(Settings(user_id=user.id))
    db.commit()
    return _token_for_user(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _token_for_user(user)


@router.post("/guest", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def create_guest(db: Session = Depends(get_db)):
    guest_id = str(uuid.uuid4())[:8]
    user = User(
        email=f"guest-{guest_id}@mcuverse.local",
        full_name="Guest Explorer",
        role="guest",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.add(Settings(user_id=user.id))
    db.commit()
    return _token_for_user(user)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
