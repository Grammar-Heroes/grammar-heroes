import re
from app.utils.profanity import is_profane

RE_USERNAME = re.compile(r"^[A-Za-z0-9_]{3,16}$")

def valid_display_name(name: str) -> bool:
    if not RE_USERNAME.fullmatch(name):
        return False
    # reject emoji or non-basic chars
    if any(ord(ch) > 0x7F for ch in name):
        return False
    if is_profane(name.lower()):
        return False
    return True