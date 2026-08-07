import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from redis.asyncio import Redis
from redis.exceptions import LockError

logger = logging.getLogger(__name__)


class UserLockMiddleware(BaseMiddleware):
    """
    Serializes update processing per Telegram user.

    aiogram dispatches concurrent updates by default, so a user spamming
    messages while in an FSM state (e.g. "describe your problem") can have
    several updates read the SAME state before any of them commits its
    transition to the next one — each update then thinks it's the first
    message and, e.g., creates its own ticket. A per-user Redis lock forces
    updates from the same user to be handled strictly one at a time, so
    every handler always sees the FSM state left by the previous update.
    """

    def __init__(self, redis: Redis, lock_timeout: int = 30, blocking_timeout: int = 15):
        super().__init__()
        self.redis = redis
        self.lock_timeout = lock_timeout
        self.blocking_timeout = blocking_timeout

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is None:
            return await handler(event, data)

        lock = self.redis.lock(
            f"user_lock:{user.id}",
            timeout=self.lock_timeout,
            blocking_timeout=self.blocking_timeout,
        )
        try:
            async with lock:
                return await handler(event, data)
        except LockError:
            logger.warning(f"Could not acquire per-user lock for {user.id} in time, dropping update")
            return None
