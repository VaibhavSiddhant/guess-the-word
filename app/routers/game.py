import random
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..game_logic import MAX_GAMES_PER_DAY, MAX_GUESSES, evaluate
from ..models import (
    ROLE_PLAYER, STATUS_IN_PROGRESS, STATUS_LOST, STATUS_WON, Game, Guess, User, Word,
)
from ..schemas import GameState, GuessIn, PlayerStatus
from ..security import get_current_user

router = APIRouter(prefix="/api/game", tags=["game"])


def require_player(user: User = Depends(get_current_user)) -> User:
    if user.role != ROLE_PLAYER:
        raise HTTPException(403, "Only players can play the game")
    return user


def _state(game: Game) -> GameState:
    finished = game.status != STATUS_IN_PROGRESS
    return GameState(
        game_id=game.id,
        status=game.status,
        guesses=[{"guess": g.guess_text, "result": g.result.split(",")} for g in game.guesses],
        guesses_left=MAX_GUESSES - len(game.guesses),
        answer=game.word.text if finished else None,
    )


def _games_today(db: Session, user: User) -> int:
    return db.query(Game).filter(Game.user_id == user.id, Game.play_date == date.today()).count()


def _active_game(db: Session, user: User) -> Game | None:
    return (
        db.query(Game)
        .filter(Game.user_id == user.id, Game.status == STATUS_IN_PROGRESS)
        .order_by(Game.id.desc())
        .first()
    )


@router.get("/status", response_model=PlayerStatus)
def status(user: User = Depends(require_player), db: Session = Depends(get_db)):
    active = _active_game(db, user)
    used = _games_today(db, user)
    return PlayerStatus(
        games_today=used,
        games_remaining_today=max(0, MAX_GAMES_PER_DAY - used),
        active_game=_state(active) if active else None,
    )


@router.post("/start", response_model=GameState, status_code=201)
def start(user: User = Depends(require_player), db: Session = Depends(get_db)):
    active = _active_game(db, user)
    if active:  # resume an unfinished game instead of using up another word
        return _state(active)
    if _games_today(db, user) >= MAX_GAMES_PER_DAY:
        raise HTTPException(
            429, f"Daily limit reached: {MAX_GAMES_PER_DAY} words per day. Come back tomorrow."
        )
    words = db.query(Word).all()
    if not words:
        raise HTTPException(500, "No words configured")
    game = Game(user_id=user.id, word_id=random.choice(words).id, play_date=date.today())
    db.add(game)
    db.commit()
    db.refresh(game)
    return _state(game)


@router.post("/{game_id}/guess", response_model=GameState)
def guess(game_id: int, body: GuessIn, user: User = Depends(require_player), db: Session = Depends(get_db)):
    game = db.get(Game, game_id)
    if game is None or game.user_id != user.id:
        raise HTTPException(404, "Game not found")
    if game.status != STATUS_IN_PROGRESS:
        raise HTTPException(409, "This game is already over")

    result = evaluate(game.word.text, body.guess)
    db.add(Guess(
        game_id=game.id,
        guess_no=len(game.guesses) + 1,
        guess_text=body.guess,
        result=",".join(result),
    ))
    db.flush()
    db.refresh(game)
    if body.guess == game.word.text:
        game.status = STATUS_WON
    elif len(game.guesses) >= MAX_GUESSES:
        game.status = STATUS_LOST
    db.commit()
    db.refresh(game)
    return _state(game)
