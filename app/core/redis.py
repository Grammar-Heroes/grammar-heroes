from redis.asyncio import Redis
from app.core.config import settings

redis = Redis.from_url(settings.REDIS_URL or "redis://localhost:6379/0", encoding="utf-8", decode_responses=True)