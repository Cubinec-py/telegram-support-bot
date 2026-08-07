import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from bot.config import settings
from bot.database.database import engine, async_session_maker, init_db
from bot.handlers import user_handlers, manager_handlers
from bot.middlewares.db_middleware import DatabaseMiddleware
from bot.middlewares.rate_limit_middleware import RateLimitMiddleware
from bot.middlewares.user_lock_middleware import UserLockMiddleware
from bot.utils.scheduler import start_ticket_auto_close_scheduler

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to start the bot"""
    logger.info("Starting bot...")

    # Initialize database
    await init_db(engine)
    logger.info("Database initialized")

    # Initialize Redis
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    storage = RedisStorage(redis)
    logger.info("Redis storage initialized")

    # Initialize bot and dispatcher
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=storage)

    # Register middleware
    # Order matters: rate limit drops flood before it even tries for the lock,
    # then the per-user lock serializes whatever's left so FSM-state races
    # (e.g. a spammed message creating multiple tickets) can't happen.
    rate_limit_middleware = RateLimitMiddleware(redis)
    user_lock_middleware = UserLockMiddleware(redis)
    for observer in (dp.message, dp.callback_query):
        observer.middleware(rate_limit_middleware)
        observer.middleware(user_lock_middleware)
    dp.update.middleware(DatabaseMiddleware(async_session_maker))

    # Register routers
    dp.include_router(user_handlers.router)
    dp.include_router(manager_handlers.router)

    logger.info("Handlers registered")

    # Start ticket auto-close scheduler
    scheduler_task = asyncio.create_task(
        start_ticket_auto_close_scheduler(async_session_maker, bot)
    )
    logger.info("Auto-close scheduler started")

    try:
        # Start polling
        logger.info("Bot started successfully")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler_task.cancel()
        await bot.session.close()
        await redis.close()
        await engine.dispose()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")

