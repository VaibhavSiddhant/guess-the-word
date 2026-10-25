from app.database import SessionLocal
from app.game_logic import SEED_WORDS, evaluate
from app.models import Game


def secret_of(game_id):
    with SessionLocal() as db:
        return db.get(Game, game_id).word.text


def wrong_word(secret):
    return "ZZZZZ" if secret != "ZZZZZ" else "YYYYY"


# ---- feedback colours ----
def test_evaluate_all_green():
    assert evaluate("TOWER", "TOWER") == ["green"] * 5


def test_evaluate_matches_screenshot():
    assert evaluate("TOWER", "AUDIO") == ["grey"] * 4 + ["orange"]
    assert evaluate("TOWER", "HOMER") == ["grey", "green", "grey", "green", "green"]
    assert evaluate("TOWER", "TONER") == ["green", "green", "grey", "green", "green"]


def test_evaluate_duplicate_letters():
    # CRANE has one E, already claimed by the green E at the end: the other Es are grey
    assert evaluate("CRANE", "EERIE") == ["grey", "grey", "orange", "grey", "green"]


def test_twenty_words_seeded():
    assert len(SEED_WORDS) == 20 and all(len(w) == 5 and w.isupper() for w in SEED_WORDS)


# ---- registration / login ----
def test_register_validation(client):
    bad = [
        ("abc", "pass$123"),       # short username
        ("user1234", "pass$123"),  # digits in username
        ("Validname", "ab$1"),     # short password
        ("Validname", "abcde$$$"), # no digit
        ("Validname", "abc12345"), # no special
        ("Validname", "12345$$$"), # no letter
    ]
    for u, p in bad:
        assert client.post("/api/auth/register", json={"username": u, "password": p}).status_code == 422


def test_duplicate_and_login(client, player):
    name, _ = player
    assert client.post("/api/auth/register", json={"username": name, "password": "pass$123"}).status_code == 409
    assert client.post("/api/auth/login", json={"username": name, "password": "wrong$1"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": name, "password": "pass$123"}).status_code == 200


# ---- gameplay ----
def test_win(client, player):
    _, h = player
    g = client.post("/api/game/start", headers=h).json()
    secret = secret_of(g["game_id"])
    r = client.post(f"/api/game/{g['game_id']}/guess", json={"guess": secret}, headers=h).json()
    assert r["status"] == "WON" and r["answer"] == secret
    assert client.post(f"/api/game/{g['game_id']}/guess", json={"guess": secret}, headers=h).status_code == 409


def test_lose_after_five_and_history_kept(client, player):
    _, h = player
    g = client.post("/api/game/start", headers=h).json()
    bad = wrong_word(secret_of(g["game_id"]))
    for i in range(1, 6):
        r = client.post(f"/api/game/{g['game_id']}/guess", json={"guess": bad}, headers=h).json()
        assert len(r["guesses"]) == i
    assert r["status"] == "LOST" and r["answer"] is not None and r["guesses_left"] == 0


def test_guess_must_be_five_uppercase_letters(client, player):
    _, h = player
    g = client.post("/api/game/start", headers=h).json()
    for bad in ["abcde", "ABCD", "ABCDEF", "AB1DE"]:
        assert client.post(f"/api/game/{g['game_id']}/guess", json={"guess": bad}, headers=h).status_code == 422


def test_unfinished_game_is_resumed(client, player):
    _, h = player
    a = client.post("/api/game/start", headers=h).json()
    b = client.post("/api/game/start", headers=h).json()
    assert a["game_id"] == b["game_id"]


def test_daily_limit_three(client, player):
    _, h = player
    for _ in range(3):
        g = client.post("/api/game/start", headers=h).json()
        client.post(f"/api/game/{g['game_id']}/guess", json={"guess": secret_of(g["game_id"])}, headers=h)
    assert client.post("/api/game/start", headers=h).status_code == 429
    assert client.get("/api/game/status", headers=h).json()["games_remaining_today"] == 0


def test_cannot_touch_other_users_game(client, player):
    _, h1 = player
    g = client.post("/api/game/start", headers=h1).json()
    r = client.post("/api/auth/register", json={"username": "Intruder", "password": "pass$123"})
    h2 = {"Authorization": "Bearer " + r.json()["access_token"]}
    assert client.post(f"/api/game/{g['game_id']}/guess", json={"guess": "APPLE"}, headers=h2).status_code == 404


# ---- admin reports ----
def test_reports(client, player, admin):
    name, h = player
    for win in (True, False):
        g = client.post("/api/game/start", headers=h).json()
        s = secret_of(g["game_id"])
        client.post(f"/api/game/{g['game_id']}/guess", json={"guess": s if win else wrong_word(s)}, headers=h)
        if not win:  # finish the losing game so the next one can start
            for _ in range(4):
                client.post(f"/api/game/{g['game_id']}/guess", json={"guess": wrong_word(s)}, headers=h)

    u = client.get("/api/admin/reports/user", params={"username": name}, headers=admin).json()
    assert u["rows"][0]["words_tried"] == 2 and u["rows"][0]["correct_guesses"] == 1

    d = client.get("/api/admin/reports/day", headers=admin).json()
    assert d["users_played"] >= 1 and d["correct_guesses"] >= 1


def test_role_separation(client, player, admin):
    _, h = player
    assert client.get("/api/admin/reports/day", headers=h).status_code == 403
    assert client.post("/api/game/start", headers=admin).status_code == 403
    assert client.get("/api/admin/reports/day").status_code == 401
