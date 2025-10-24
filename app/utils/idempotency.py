from app.core.redis import redis

async def ensure_idempotent(key: str, ttl_seconds: int = 300) -> bool:
    # returns True if we successfully claim the key; False if already processed
    claimed = await redis.setnx(f"idem:{key}", "1")
    if claimed:
        await redis.expire(f"idem:{key}", ttl_seconds)
        return True
    return False