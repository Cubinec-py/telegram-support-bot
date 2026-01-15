from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
from sqlalchemy.pool import NullPool
from bot.config import settings
from bot.database.models import Base


# Main database engine
engine = create_async_engine(
    settings.database_url,
    echo=False,
    poolclass=NullPool,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Optional game database engine
game_engine = None
game_session_maker = None

if settings.GAME_DB_ENABLED and settings.game_database_url:
    game_engine = create_async_engine(
        settings.game_database_url,
        echo=False,
        poolclass=NullPool,
    )
    game_session_maker = async_sessionmaker(
        game_engine,
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


async def get_game_session() -> AsyncSession:
    """Get game database session if enabled"""
    if game_session_maker:
        async with game_session_maker() as session:
            yield session
    else:
        yield None

