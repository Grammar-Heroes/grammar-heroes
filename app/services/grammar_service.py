import logging
import re
from typing import Dict, List, Optional, Any

import httpx

from app.utils.normalize import normalize_sentence
from app.utils.redis_cache import get_sentence_cache, set_sentence_cache
from app.core.config import settings


logger = logging.getLogger("grammar_cache")

T5_API_URL = settings.T5_API_URL
T5_API_KEY = settings.T5_API_KEY


# ---------------- Kid-Friendly Error Messages ----------------
ERROR_FRIENDLY: Dict[str, str] = {
    # Missing
    "M:PART": "A word is missing.",
    "M:PUNCT": "You forgot punctuation.",
    "M:CONJ": "A joining word is missing.",
    "M:DET": "A helper word is missing.",
    "M:DET:ART": "You need a, an, or the.",
    "M:PREP": "A place word is missing.",
    "M:PRON": "A name word is missing.",
    "M:VERB": "An action word is missing.",
    "M:ADJ": "A describing word is missing.",
    "M:NOUN": "A thing word is missing.",
    "M:NOUN:POSS": "You need 's here.",
    "M:OTHER": "Something is missing.",

    # Needs fixing
    "R:PART": "This word doesn’t fit.",
    "R:PUNCT": "The punctuation needs fixing.",
    "R:ORTH": "This spelling looks wrong.",
    "R:SPELL": "Spelling mistake here.",
    "R:WO": "Words are in the wrong order.",
    "R:MORPH": "This word sounds wrong.",
    "R:ADV": "Use a word ending in -ly.",
    "R:CONTR": "The shortened word is wrong.",
    "R:CONJ": "The joining word is wrong.",
    "R:DET": "The helper word is wrong.",
    "R:DET:ART": "Use a, an, or the correctly.",
    "R:PREP": "The place word is wrong.",
    "R:PRON": "The name word is wrong.",
    "R:VERB:FORM": "The action word needs changing.",
    "R:VERB:TENSE": "The time of the action is wrong.",
    "R:VERB:SVA": "This verb doesn’t match the subject.",
    "R:ADJ:FORM": "The describing word needs fixing.",
    "R:NOUN:INFL": "The plural is wrong.",
    "R:NOUN:NUM": "The number word is wrong.",
    "R:OTHER": "This part needs fixing.",

    # Extra / remove it
    "U:PART": "There’s an extra word.",
    "U:PUNCT": "There’s extra punctuation.",
    "U:ADV": "There’s an extra -ly word.",
    "U:CONTR": "There’s an extra shortened word.",
    "U:CONJ": "There’s an extra joining word.",
    "U:DET": "There’s an extra helper word.",
    "U:DET:ART": "There’s an extra a, an, or the.",
    "U:PREP": "There’s an extra place word.",
    "U:PRON": "There’s an extra name word.",
    "U:VERB": "There’s an extra action word.",
    "U:ADJ": "There’s an extra describing word.",
    "U:NOUN": "There’s an extra thing word.",
    "U:NOUN:POSS": "There’s an extra 's.",
    "U:OTHER": "There’s something extra here.",
}

DEFAULT_FRIENDLY = "Something needs fixing."


# ---------------- T5 API Call ----------------
async def _t5_check(sentence: str) -> Dict[str, Any]:
    """Calls the external grammar model."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                T5_API_URL,
                json={
                    "key": T5_API_KEY,
                    "text": sentence,
                    "session_id": "grammar_heroes",
                },
            )
            if resp.status_code < 300:
                return resp.json()
            logger.error("T5 error %s: %s", resp.status_code, resp.text)
            return {"error": "T5 error"}
    except Exception as e:
        logger.exception("T5 check failed: %s", e)
        return {"error": f"T5 check failed: {e}"}


# ---------------- Feedback Extraction ----------------
def _extract_feedback(data: Dict[str, Any]) -> List[str]:
    """Turns Sapling edits into kid-friendly messages."""
    feedback: List[str] = []

    # Server error case
    if not data or ("error" in data and "edits" not in data):
        feedback.append(str(data.get("error", "Unknown error")))
        return feedback

    edits = data.get("edits", [])
    for edit in edits:
        error_type = edit.get("error_type", "")
        message = ERROR_FRIENDLY.get(error_type, DEFAULT_FRIENDLY)
        feedback.append(message)

    return feedback


def _extract_error_indices(sentence: str, edits: List[Dict[str, Any]]) -> List[int]:
    """Returns token indices where mistakes are located."""
    if not edits:
        return []
    tokens = list(re.finditer(r"\S+", sentence))
    error_indices = set()

    for edit in edits:
        start, end = edit.get("start", 0), edit.get("end", 0)
        for i, tok in enumerate(tokens):
            s, e = tok.span()
            if e > start and s < end:
                error_indices.add(i)

    return sorted(error_indices)


def _is_correct(data: Dict[str, Any]) -> bool:
    """Sentence is correct if there are zero edits."""
    return bool(data and "edits" in data and len(data["edits"]) == 0)


# ---------------- Public Entry ----------------
async def check_sentence(
    sentence: str,
    kc_id: Optional[int] = None,
    tier_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Main API: caching, model call, result shaping."""
    normalized = normalize_sentence(sentence)
    cached = await get_sentence_cache(normalized, kc_id)

    if cached:
        logger.info("[CACHE HIT] %s", normalized)
        cached["from_cache"] = True
        return cached

    t5_response = await _t5_check(sentence)

    feedback = _extract_feedback(t5_response)
    correct = _is_correct(t5_response)
    edits = t5_response.get("edits", []) if t5_response else []
    indices = _extract_error_indices(sentence, edits)

    result = {
        "is_correct": correct,
        "error_indices": indices,
        "feedback": feedback,
        "scores": {"t5_edits": len(edits)},
        "candidates": [],
        "best_candidate": sentence,  # placeholder until KC bank returns
        "from_cache": False,
    }

    await set_sentence_cache(normalized, kc_id, result)
    return result