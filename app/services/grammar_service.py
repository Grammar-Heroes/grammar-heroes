# app/services/grammar_service.py
import logging, re, httpx
from typing import Dict, List, Optional
from app.utils.normalize import normalize_sentence
from app.utils.redis_cache import get_sentence_cache, set_sentence_cache
from app.core.config import settings
# from app.services.kc_answer_bank import contains as bank_contains, best_match as bank_best_match


logger = logging.getLogger("grammar_cache")

TFIVEBASE = settings.TFIVEBASE


# ---------------- Sapling Call ----------------
async def _sapling_check(sentence: str) -> Optional[Dict]:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                TFIVEBASE,
                json={"key": TFIVEBASE, "text": sentence, "session_id": "grammar_heroes"},
            )
            if 200 <= resp.status_code < 300:
                return resp.json()
            else:
                logger.error(f"T5 error")
                return {"error": f"T5 error"}
    except Exception as e:
        logger.exception("T5 failed: %s", e)
        return {"error"}


# ---------------- Feedback helpers ----------------
def _extract_feedback(data: Dict) -> List[str]:
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
        wrong = old_sentence[start:end]
        if wrong and replacement:
            feedback.append(f"Replace '{wrong}' with '{replacement}'")
        elif wrong and not replacement:
            feedback.append(f"Remove '{wrong}'")
    return feedback


def _extract_error_indices(sentence: str, edits: List[Dict]) -> List[int]:
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


def _is_correct(data: Dict) -> bool:
    return bool(data and "edits" in data and len(data["edits"]) == 0)


# ---------------- Public entry ----------------
async def check_sentence(sentence: str, kc_id: Optional[int] = None) -> Dict[str, object]:
    """Main grammar check with Sapling + Redis cache."""
    normalized = normalize_sentence(sentence)
    cached = await get_sentence_cache(normalized, kc_id)
    if cached:
        logger.info("[CACHE HIT] %s", normalized)
        cached["from_cache"] = True
        return cached

    sapling = await _sapling_check(sentence)
    feedback = _extract_feedback(sapling)
    correct = _is_correct(sapling)
    edits = sapling.get("edits", []) if sapling else []
    indices = _extract_error_indices(sentence, edits)

    result = {
        "is_correct": correct,
        "error_indices": indices,
        "feedback": feedback,
        "scores": {"sapling_edits": len(edits)},
        "candidates": [],
        "best_candidate": sentence,
        "from_cache": False,
    }

    await set_sentence_cache(normalized, kc_id, result)
    return result


# New System
# async def check_sentence(sentence: str, kc_id: Optional[int] = None, tier_id: Optional[int] = None) -> Dict[str, object]:
#     normalized = normalize_sentence(sentence)
#     cached = await get_sentence_cache(normalized, kc_id)
#     if cached:
#         logger.info("[CACHE HIT] %s", normalized)
#         cached["from_cache"] = True
#         return cached

#     # ---------- KC/Tier membership short-circuit ----------
#     if kc_id is not None and bank_contains(int(kc_id), sentence, tier_id):
#         result = {
#             "is_correct": True,
#             "error_indices": [],
#             "feedback": [],
#             "scores": {"sapling_edits": 0},
#             "candidates": [],
#             "best_candidate": sentence,
#             "from_cache": False,
#         }
#         await set_sentence_cache(normalized, kc_id, result)
#         return result

#     # ---------- fall through to existing checker (Sapling/T5 later) ----------
#     sapling = await _sapling_check(sentence)
#     feedback = _extract_feedback(sapling)
#     correct = _is_correct(sapling)
#     edits = sapling.get("edits", []) if sapling else []
#     indices = _extract_error_indices(sentence, edits)

#     result = {
#         "is_correct": correct,
#         "error_indices": indices,
#         "feedback": feedback,
#         "scores": {"sapling_edits": len(edits)},
#         "candidates": [],
#         "best_candidate": (bank_best_match(int(kc_id), sentence, tier_id) if kc_id else sentence),
#         "from_cache": False,
#     }
#     await set_sentence_cache(normalized, kc_id, result)
#     return result