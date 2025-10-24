# app/utils/redis_cache.py
from __future__ import annotations
import json, time, hashlib
from typing import Optional, Dict, Tuple, TYPE_CHECKING, Any
from app.core.config import settings

if TYPE_CHECKING:
    from redis.asyncio.client import Redis as RedisType
else:
    RedisType = Any  # runtime-safe fallback

try:
    from redis.asyncio import from_url as redis_from_url
except Exception:
    redis_from_url = None  # redis not installed/unavailable

_redis: Optional[RedisType] = None
_fallback: Dict[str, Tuple[float, str]] = {}
_TTL_DEFAULT = 30 * 24 * 60 * 60  # 30 days

def _key(sentence: str, kc_id: Optional[int]) -> str:
    h = hashlib.sha256(sentence.encode("utf-8")).hexdigest()
    return f"gh:sapling:{kc_id or 0}:{h}"

async def _client() -> Optional[RedisType]:
    global _redis
    if _redis is not None:
        return _redis
    url = settings.REDIS_URL
    if not url or not redis_from_url:
        return None
    try:
        _redis = redis_from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
        )
        await _redis.ping()
        return _redis
    except Exception:
        _redis = None
        return None

async def get_sentence_cache(sentence: str, kc_id: Optional[int]):
    key = _key(sentence, kc_id)
    client = await _client()
    if client:
        try:
            val = await client.get(key)
            return json.loads(val) if val else None
        except Exception:
            pass
    itm = _fallback.get(key)
    if itm and itm[0] > time.time():
        return json.loads(itm[1])
    return None

async def set_sentence_cache(sentence: str, kc_id: Optional[int], value: dict, ttl_days: int = 30):
    key = _key(sentence, kc_id)
    s = json.dumps(value)
    client = await _client()
    if client:
        try:
            await client.set(key, s, ex=ttl_days * 24 * 60 * 60)
            return
        except Exception:
            pass
    _fallback[key] = (time.time() + _TTL_DEFAULT, s)