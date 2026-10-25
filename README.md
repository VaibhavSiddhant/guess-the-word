# Guess the Word

A Wordle-style game built with **FastAPI**, SQLAlchemy (SQLite) and a small vanilla-JS front end.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 (API docs at `/docs`).

On first start the app creates `wordgame.db`, loads 20 five-letter words and creates an admin account:

| Role   | Username | Password   |
|--------|----------|------------|
| Admin  | `Admin`  | `Admin$123` |
| Player | register from the login page | |

Override with env vars `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `SECRET_KEY`, `DATABASE_URL`.

## Run the tests

```bash
pytest
```

## Rules implemented

- **Registration:** username = at least 5 letters (A-Z, a-z only). Password = at least 5 characters with a letter, a digit and one of `$ % *`.
- **Words:** 20 upper-case 5-letter words stored in the `words` table.
- **Play:** a random word is picked per game. Max **3 words per user per day** (server date). An unfinished game is resumed instead of using another word.
- **Guesses:** 5 upper-case letters, max 5 guesses. Green = right letter, right spot. Orange = right letter, wrong spot. Grey = not in the word. Repeated letters are coloured only as many times as they appear in the answer.
- **End of game:** win shows a congratulations message, using all 5 guesses shows "Better luck next time"; clicking OK stops the game.
- **Stored data:** every game (user, word, date, status) and every guess with its colours are saved in `games` and `guesses`.
- **Admin reports:** by day (users who played, words given, correct guesses) and by user (date, words tried, correct guesses).

## API

| Method | Path | Who |
|---|---|---|
| POST | `/api/auth/register`, `/api/auth/login` | anyone |
| GET | `/api/game/status` | player |
| POST | `/api/game/start` | player |
| POST | `/api/game/{id}/guess` | player |
| GET | `/api/admin/reports/day?date=YYYY-MM-DD` | admin |
| GET | `/api/admin/reports/user?username=...` | admin |

## Layout

```
app/        FastAPI app (models, schemas, security, game_logic, routers/)
static/     index.html, style.css, app.js
tests/      pytest suite
```
