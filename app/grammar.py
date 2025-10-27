import json
import logging
import re
from typing import Dict, List, Optional
import httpx

from app.utils.normalize import normalize_sentence
from app.utils.redis_cache import get_sentence_cache, set_sentence_cache
from app.core.config import settings

logger = logging.getLogger("grammar_cache")

SAPLING_API_URL = "https://api.sapling.ai/api/v1/edits"
SAPLING_API_KEY = settings.SAPLING_API_KEY


# -------------------------------
# Sapling Request Logic
# -------------------------------
async def _sapling_check(sentence: str) -> Optional[Dict]:
    """Send a grammar check request to Sapling API."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                SAPLING_API_URL,
                json={
                    "key": SAPLING_API_KEY,
                    "text": sentence,
                    "session_id": "grammar_heroes",
                },
            )

            if 200 <= resp.status_code < 300:
                return resp.json()
            else:
                logger.error(f"Sapling API error {resp.status_code}: {resp.text}")
                return {"error": f"Sapling API error {resp.status_code}: {resp.text}"}

    except Exception as e:
        logger.exception("Sapling API call failed: %s", e)
        return {"error": str(e)}


# -------------------------------
# Postprocessing and Scoring
# -------------------------------
def _extract_feedback(data: Dict) -> List[str]:
    """Convert Sapling edits into human-readable feedback."""
    feedback = []
    if not data or "edits" not in data:
        if "error" in data:
            feedback.append(data["error"])
        return feedback

    for edit in data.get("edits", []):
        old_sentence = edit.get("sentence", "")
        start = edit.get("start", 0)
        end = edit.get("end", 0)
        replacement = edit.get("replacement", "")
        wrong_part = old_sentence[start:end]
        if wrong_part and replacement:
            feedback.append(f"Replace '{wrong_part}' with '{replacement}'")
        elif wrong_part and not replacement:
            feedback.append(f"Remove '{wrong_part}'")
    return feedback


def _extract_error_indices(sentence: str, edits: List[Dict]) -> List[int]:
    """Convert Sapling character offsets to token indices."""
    if not edits:
        return []

    tokens = list(re.finditer(r"\S+", sentence))
    error_indices = set()

    for edit in edits:
        start = edit.get("start", 0)
        end = edit.get("end", 0)
        for i, token in enumerate(tokens):
            token_start, token_end = token.span()
            # overlap check
            if token_end > start and token_start < end:
                error_indices.add(i)

    return sorted(error_indices)


def _is_grammatically_correct(data: Dict) -> bool:
    """Heuristic: if Sapling returns no edits, it's correct."""
    if not data or "edits" not in data:
        return False
    return len(data["edits"]) == 0


# -------------------------------
# Main Entry
# -------------------------------
async def check_sentence(sentence: str, kc_id: Optional[int] = None) -> Dict[str, object]:
    """Main grammar check function with Redis cache and Sapling integration."""
    normalized = normalize_sentence(sentence)
    cached = await get_sentence_cache(normalized, kc_id)

    if cached:
        logger.info("[CACHE HIT] '%s'", normalized)
        cached["from_cache"] = True
        return cached

    logger.info("[CACHE MISS] '%s'", normalized)
    sapling_result = await _sapling_check(sentence)

    feedback = _extract_feedback(sapling_result)
    is_correct = _is_grammatically_correct(sapling_result)
    edits = sapling_result.get("edits", []) if sapling_result else []

    # Map edits → token indices
    error_indices = _extract_error_indices(sentence, edits)

    result: Dict[str, object] = {
        "is_correct": is_correct,
        "error_indices": error_indices,
        "feedback": feedback,
        "scores": {
            "sapling_edits": len(edits),
        },
        "candidates": [],
        "best_candidate": sentence,
        "from_cache": False,
    }

    # Cache result for 30 days
    await set_sentence_cache(normalized, kc_id, result)
    return result