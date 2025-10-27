# from __future__ import annotations
# import json, os, re
# from typing import Dict, Set, Optional, List, Tuple

# _ANSWERS: Dict[int, Dict[int, Set[str]]] = {}
# _LOADED = False

# def _normalize(s: str) -> str:
#     s = s.strip()
#     s = re.sub(r"\s+", " ", s)
#     if s and not s.endswith("."):
#         s += "."
#     if s:
#         s = s[0].upper() + s[1:]
#     return s

# def _load_once() -> None:
#     global _LOADED, _ANSWERS
#     if _LOADED:
#         return
#     path = os.getenv(
#         "KC_ANSWERS_PATH",
#         os.path.join(os.path.dirname(__file__), "..", "content", "answers.json"),
#     )
#     path = os.path.abspath(path)
#     if not os.path.exists(path):
#         _ANSWERS = {}
#         _LOADED = True
#         return
#     with open(path, "r", encoding="utf-8") as f:
#         raw = json.load(f)
#     out: Dict[int, Dict[int, Set[str]]] = {}
#     for kc_str, tiers in raw.items():
#         kc = int(kc_str)
#         out[kc] = {}
#         for tier_str, items in tiers.items():
#             tier = int(tier_str)
#             out[kc][tier] = { _normalize(x) for x in items }
#     _ANSWERS = out
#     _LOADED = True

# def contains(kc_id: int, sentence: str, tier_id: Optional[int] = None) -> bool:
#     _load_once()
#     s = _normalize(sentence)
#     tiers = _ANSWERS.get(kc_id, {})
#     if tier_id and tier_id in tiers:
#         return s in tiers[tier_id]
#     return any(s in bank for bank in tiers.values())

# def best_match(kc_id: int, sentence: str, tier_id: Optional[int] = None) -> Optional[str]:
#     _load_once()
#     tiers = _ANSWERS.get(kc_id, {})
#     if not tiers:
#         return None
#     s = _normalize(sentence)
#     stoks = s.lower().split()
#     cands: List[str] = []
#     if tier_id and tier_id in tiers:
#         cands = list(tiers[tier_id])
#     else:
#         for bank in tiers.values():
#             cands.extend(list(bank))
#     if not cands:
#         return None
#     def score(c: str) -> Tuple[int, int]:
#         ct = c.lower().split()
#         overlap = len(set(ct) & set(stoks))
#         delta = abs(len(ct) - len(stoks))
#         return (overlap, -delta)
#     cands.sort(key=score, reverse=True)
#     return cands[0]