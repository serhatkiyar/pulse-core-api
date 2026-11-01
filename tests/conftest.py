import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.config import settings
from app.database import get_db
from app.main import app
from app.models import Base
from app.oauth2 import create_token

engine = create_engine(
    f"postgresql+psycopg2://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}/{settings.DATABASE_NAME}_test"
)

TestingLocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingLocalSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(session):
    def get_test_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = get_test_db
    yield TestClient(app)


@pytest.fixture
def test_user(client):
    user_data = {
        "name": "Serhat",
        "email": "serhat@gmail.com",
        "password": "password123",
    }
    res = client.post("/users/", json=user_data)
    assert res.status_code == 201
    new_user = res.json()
    new_user["password"] = user_data["password"]
    return new_user


@pytest.fixture
def test_user2(client):
    user_data = {
        "name": "Ahmet",
        "email": "ahmet@gmail.com",
        "password": "password123",
    }
    res = client.post("/users/", json=user_data)
    assert res.status_code == 201
    new_user = res.json()
    new_user["password"] = user_data["password"]
    return new_user


@pytest.fixture
def token(test_user):
    return create_token({"user_id": test_user["id"]})


@pytest.fixture
def authorized_client(client, token):
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token}",
    }
    return client


@pytest.fixture
def test_posts(test_user, session, test_user2):
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

    post_models = [models.Post(**post) for post in posts_data]
    session.add_all(post_models)
    session.commit()

    posts = session.query(models.Post).order_by(models.Post.id).all()
    return posts
