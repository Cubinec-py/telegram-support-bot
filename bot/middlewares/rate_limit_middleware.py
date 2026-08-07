from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from redis.asyncio import Redis


class RateLimitMiddleware(BaseMiddleware):
    """Drops updates from a user once they exceed `limit` updates within
    `window_seconds`, so a single user flooding the ticket conversation can't
    hammer the DB/notification pipeline. Silently drops rather than replying,
    since replying to every flooded message would itself be part of the flood."""

    def __init__(self, redis: Redis, limit: int = 20, window_seconds: int = 10):
        super().__init__()
        self.redis = redis
        self.limit = limit
        self.window_seconds = window_seconds

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is None:
            return await handler(event, data)

        key = f"rate_limit:{user.id}"
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, self.window_seconds)

        if count > self.limit:
            return None

        return await handler(event, data)
