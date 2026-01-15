import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.config import settings
from bot.database.database import init_db
from bot.handlers import user_handlers, manager_handlers
from bot.middlewares.db_middleware import DatabaseMiddleware
from bot.utils.scheduler import start_ticket_auto_close_scheduler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to start the bot"""
    logger.info("Starting bot...")

    # Initialize database
    engine = create_async_engine(settings.database_url, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

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
    dp.update.middleware(DatabaseMiddleware(session_maker))

    # Register routers
    dp.include_router(user_handlers.router)
    dp.include_router(manager_handlers.router)

    logger.info("Handlers registered")

    # Start ticket auto-close scheduler
    scheduler_task = asyncio.create_task(
        start_ticket_auto_close_scheduler(session_maker, bot)
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

