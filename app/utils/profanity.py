# app/utils/profanity.py
# Tiny placeholder list. Replace with a fuller dataset as needed.
_BAD = {
    "badword",
    "dummy",
}

def is_profane(text: str) -> bool:
    return any(b in text for b in _BAD)