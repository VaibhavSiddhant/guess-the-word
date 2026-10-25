from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ROLE_PLAYER, User
from ..schemas import LoginIn, RegisterIn, TokenOut
from ..security import create_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _token_out(user: User) -> TokenOut:
    return TokenOut(access_token=create_token(user), username=user.username, role=user.role)


@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    exists = db.query(User).filter(func.lower(User.username) == body.username.lower()).first()
    if exists:
        raise HTTPException(409, "That username is taken")
    user = User(username=body.username, password_hash=hash_password(body.password), role=ROLE_PLAYER)
    db.add(user)
    db.commit()
    db.refresh(user)
    return _token_out(user)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Wrong username or password")
    return _token_out(user)
