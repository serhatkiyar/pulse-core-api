from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .config import settings

SQL_ALCHEMY_URL = f"postgresql+asyncpg://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}/{settings.DATABASE_NAME}"
engine = create_async_engine(SQL_ALCHEMY_URL, echo=True)


async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        yield session
