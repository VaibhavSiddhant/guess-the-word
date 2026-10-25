from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base

ROLE_ADMIN = "admin"
ROLE_PLAYER = "player"

STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_WON = "WON"
STATUS_LOST = "LOST"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(10), nullable=False, default=ROLE_PLAYER)


class Word(Base):
    __tablename__ = "words"
    id = Column(Integer, primary_key=True)
    text = Column(String(5), unique=True, nullable=False)


class Game(Base):
    """One word given to one user on one day."""
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    play_date = Column(Date, nullable=False, default=date.today, index=True)
    status = Column(String(12), nullable=False, default=STATUS_IN_PROGRESS)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    word = relationship("Word")
    guesses = relationship("Guess", order_by="Guess.guess_no", cascade="all, delete-orphan")


class Guess(Base):
    """A word guessed by the user for a game; `result` is e.g. 'green,grey,orange,grey,grey'."""
    __tablename__ = "guesses"
    __table_args__ = (UniqueConstraint("game_id", "guess_no"),)
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    guess_no = Column(Integer, nullable=False)
    guess_text = Column(String(5), nullable=False)
    result = Column(String(40), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
