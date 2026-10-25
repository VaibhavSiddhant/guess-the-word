import re
from datetime import date

from pydantic import BaseModel, Field, field_validator

SPECIALS = "$%*"


class RegisterIn(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def check_username(cls, v: str) -> str:
        if not re.fullmatch(r"[A-Za-z]{5,}", v):
            raise ValueError("Username must be at least 5 letters (A-Z, a-z only)")
        return v

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        if (
            len(v) < 5
            or not any(c.isalpha() for c in v)
            or not any(c.isdigit() for c in v)
            or not any(c in SPECIALS for c in v)
        ):
            raise ValueError(
                "Password must be at least 5 characters with a letter, a number "
                "and one of $, % or *"
            )
        return v


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    username: str
    role: str


class GuessIn(BaseModel):
    guess: str = Field(pattern=r"^[A-Z]{5}$", description="5 upper-case letters")


class GuessOut(BaseModel):
    guess: str
    result: list[str]


class GameState(BaseModel):
    game_id: int
    status: str
    guesses: list[GuessOut]
    guesses_left: int
    answer: str | None = None  # only revealed when the game is over


class PlayerStatus(BaseModel):
    games_today: int
    games_remaining_today: int
    active_game: GameState | None


class DayReport(BaseModel):
    date: date
    users_played: int
    games_played: int
    correct_guesses: int


class UserReportRow(BaseModel):
    date: date
    words_tried: int
    correct_guesses: int


class UserReport(BaseModel):
    username: str
    rows: list[UserReportRow]
