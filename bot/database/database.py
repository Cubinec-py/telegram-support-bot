from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
from bot.config import settings
from bot.database.models import Base


# Main database engine (pool_size/max_overflow default to SQLAlchemy's
# AsyncAdaptedQueuePool — reused connections instead of one per checkout,
# appropriate for a long-running polling bot)
engine = create_async_engine(
    settings.database_url,
    echo=False,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db(engine: AsyncEngine):
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def create_tables():
    """Create all tables in the database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Get database session"""
    async with async_session_maker() as session:
        yield session

