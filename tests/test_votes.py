import asyncio
import pytest

from app import models
from tests.conftest import TestingLocalSession


@pytest.fixture
def test_vote(test_posts, session, test_user):
    async def add_vote():
        async with TestingLocalSession() as db:
            new_vote = models.Vote(post_id=test_posts[3].id, user_id=test_user["id"])
            db.add(new_vote)
            await db.commit()

    asyncio.run(add_vote())


def test_vote_on_post(authorized_client, test_posts):
    res = authorized_client.post(
        "/vote/", json={"post_id": test_posts[3].id, "method": 1}
    )
    assert res.status_code == 201


def test_vote_twice_post(authorized_client, test_posts, test_vote):
    res = authorized_client.post(
        "/vote/", json={"post_id": test_posts[3].id, "method": 1}
    )
    assert res.status_code == 409


def test_delete_vote(authorized_client, test_posts, test_vote):
    res = authorized_client.post(
        "/vote/", json={"post_id": test_posts[3].id, "method": 0}
    )
    assert res.status_code == 201


def test_delete_vote_non_exist(authorized_client, test_posts):
    res = authorized_client.post(
        "/vote/", json={"post_id": test_posts[3].id, "method": 0}
    )
    assert res.status_code == 404


def test_vote_post_non_exist(authorized_client, test_posts):
    res = authorized_client.post("/vote/", json={"post_id": 80000, "method": 1})
    assert res.status_code == 404


def test_vote_unauthorized_user(client, test_posts):
    res = client.post("/vote/", json={"post_id": test_posts[3].id, "method": 1})
    assert res.status_code == 401
