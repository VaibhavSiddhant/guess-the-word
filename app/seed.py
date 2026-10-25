import os

from sqlalchemy.orm import Session

from .game_logic import SEED_WORDS
from .models import ROLE_ADMIN, User, Word
from .security import hash_password


def seed(db: Session) -> None:
    if db.query(Word).count() == 0:
        db.add_all(Word(text=w) for w in SEED_WORDS)
    admin_name = os.getenv("ADMIN_USERNAME", "Admin")
    if db.query(User).filter(User.username == admin_name).first() is None:
        db.add(User(
            username=admin_name,
            password_hash=hash_password(os.getenv("ADMIN_PASSWORD", "Admin$123")),
            role=ROLE_ADMIN,
        ))
    db.commit()
