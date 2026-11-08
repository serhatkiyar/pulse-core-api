import pytest
from httpx import ASGITransport, AsyncClient
from redis import asyncio as aioredis
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app import models
from app.config import settings
from app.database import get_db
from app.limiter import limiter
from app.main import app
from app.models import Base
from app.oauth2 import create_token
from app.redis import get_redis
from app.services.embedding_service import EmbeddingService

engine = create_async_engine(
    f"postgresql+asyncpg://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}/{settings.DATABASE_NAME}_test",
    poolclass=NullPool,
)

TestingLocalSession = async_sessionmaker(expire_on_commit=False, bind=engine)


class FakeEmbeddingService:
    async def get_embedding(
        self, text: str, task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> list[float]:
        return [0.1] * settings.EMBEDDING_DIMENSIONS


@pytest.fixture
async def session():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingLocalSession() as session:
        yield session


@pytest.fixture
async def client(session):
    async def get_test_db():
        async with TestingLocalSession() as db:
            yield db

    test_redis = aioredis.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )
    await test_redis.flushdb()

    async def get_test_redis():
        yield test_redis

    app.dependency_overrides[get_db] = get_test_db
    app.dependency_overrides[get_redis] = get_test_redis
    app.dependency_overrides[EmbeddingService] = lambda: FakeEmbeddingService()
    limiter.enabled = False

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    await test_redis.aclose()
    limiter.enabled = True
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(client):
    user_data = {
        "name": "Serhat",
        "email": "serhat@gmail.com",
        "password": "Password123",
    }
    res = await client.post("/users/", json=user_data)
    assert res.status_code == 201
    new_user = res.json()
    new_user["password"] = user_data["password"]
    return new_user


@pytest.fixture
async def test_user2(client):
    user_data = {
        "name": "Ahmet",
        "email": "ahmet@gmail.com",
        "password": "Password123",
    }
    res = await client.post("/users/", json=user_data)
    assert res.status_code == 201
    new_user = res.json()
    new_user["password"] = user_data["password"]
    return new_user


@pytest.fixture
def token(test_user):
    return create_token({"user_id": test_user["id"]})


@pytest.fixture
async def authorized_client(client, token):
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
async def test_posts(test_user, session: AsyncSession, test_user2):
    posts_data = [
        {
            "title": "1. başlık",
            "content": "1. içerik",
            "published": True,
            "owner_id": test_user["id"],
        },
        {
            "title": "2. başlık",
            "content": "2. içerik",
            "published": True,
            "owner_id": test_user["id"],
        },
        {
            "title": "3. başlık",
            "content": "3. içerik",
            "published": True,
            "owner_id": test_user["id"],
        },
        {
            "title": "4. başlık",
            "content": "4. içerik",
            "published": True,
            "owner_id": test_user2["id"],
        },
    ]

    async def add_posts():
        post_models = [models.Post(**post) for post in posts_data]

        session.add_all(post_models)
        await session.commit()

        query = select(models.Post).order_by(models.Post.id)
        result = await session.execute(query)
        posts = result.scalars().all()
        return posts

    return await add_posts()
