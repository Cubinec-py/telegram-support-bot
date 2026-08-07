from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories import UserRepository
from bot.config import settings


async def get_user_language(session: AsyncSession, telegram_id: int) -> str:
    """Resolve a user's (or manager's — managers are users too) saved language,
    falling back to the default when no profile exists yet."""
    user = await UserRepository(session).get_by_telegram_id(telegram_id)
    return user.language if user else settings.DEFAULT_LANGUAGE
