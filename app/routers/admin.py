from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import STATUS_WON, Game, User
from ..schemas import DayReport, UserReport
from ..security import require_admin

router = APIRouter(
    prefix="/api/admin/reports", tags=["admin"], dependencies=[Depends(require_admin)]
)


@router.get("/day", response_model=DayReport)
def day_report(
    day: date = Query(default_factory=date.today, alias="date"),
    db: Session = Depends(get_db),
):
    games = db.query(Game).filter(Game.play_date == day)
    users_played = (
        db.query(func.count(func.distinct(Game.user_id))).filter(Game.play_date == day).scalar()
    )
    return DayReport(
        date=day,
        users_played=users_played or 0,
        games_played=games.count(),
        correct_guesses=games.filter(Game.status == STATUS_WON).count(),
    )


@router.get("/user", response_model=UserReport)
def user_report(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(func.lower(User.username) == username.lower()).first()
    if user is None:
        raise HTTPException(404, "No such user")
    won = func.sum(case((Game.status == STATUS_WON, 1), else_=0))
    rows = (
        db.query(Game.play_date, func.count(Game.id), won)
        .filter(Game.user_id == user.id)
        .group_by(Game.play_date)
        .order_by(Game.play_date.desc())
        .all()
    )
    return UserReport(
        username=user.username,
        rows=[{"date": d, "words_tried": n, "correct_guesses": int(w or 0)} for d, n, w in rows],
    )
