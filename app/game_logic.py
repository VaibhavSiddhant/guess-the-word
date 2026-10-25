from collections import Counter

GREEN, ORANGE, GREY = "green", "orange", "grey"
WORD_LENGTH = 5
MAX_GUESSES = 5
MAX_GAMES_PER_DAY = 3

SEED_WORDS = [
    "APPLE", "BRAVE", "CRANE", "DREAM", "EAGLE", "FLAME", "GRAPE", "HOUSE", "IMAGE", "JOKER",
    "KNIFE", "LEMON", "MANGO", "NIGHT", "OCEAN", "PIANO", "QUEEN", "RIVER", "STONE", "TIGER",
]


def evaluate(secret: str, guess: str) -> list[str]:
    """Wordle-style feedback. Repeated letters are only marked as often as they
    occur in the secret word (greens are claimed first, then oranges left to right)."""
    result = [GREY] * WORD_LENGTH
    unmatched = Counter()
    for i, (s, g) in enumerate(zip(secret, guess)):
        if s == g:
            result[i] = GREEN
        else:
            unmatched[s] += 1
    for i, g in enumerate(guess):
        if result[i] != GREEN and unmatched[g] > 0:
            result[i] = ORANGE
            unmatched[g] -= 1
    return result
