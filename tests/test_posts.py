import pytest

from app import schemas


def test_get_all_posts(authorized_client, test_posts):
    res = authorized_client.get("/posts/")
    assert len(res.json()) == len(test_posts)
    assert res.status_code == 200


def test_unauthorized_user_get_all_posts(client, test_posts):
    res = client.get("/posts/")
    assert res.status_code == 401


def test_unauthorized_user_get_one_post(client, test_posts):
    res = client.get(f"/posts/{test_posts[0].id}")
    assert res.status_code == 401


def test_get_one_post_not_exist(authorized_client, test_posts):
    res = authorized_client.get("/posts/88888")
    assert res.status_code == 404


def test_get_one_post(authorized_client, test_posts):
    res = authorized_client.get(f"/posts/{test_posts[0].id}")
    post = schemas.PostResponse(**res.json())
    assert post.id == test_posts[0].id
    assert post.content == test_posts[0].content
    assert post.title == test_posts[0].title


@pytest.mark.parametrize(
    "title, content, published",
    [
        ("yeni başlık 1", "yeni içerik 1", True),
        ("favori pizza", "peynirli pizza", False),
        ("en yüksek gökdelen", "harika manzara", True),
    ],
)
def test_create_post(
    authorized_client, test_user, test_posts, title, content, published
):
    res = authorized_client.post(
        "/posts/",
        json={"title": title, "content": content, "published": published},
    )
    created_post = schemas.PostResponse(**res.json())
    assert res.status_code == 201
    assert created_post.title == title
    assert created_post.content == content
    assert created_post.published == published
    assert created_post.owner_id == test_user["id"]


def test_unauthorized_user_create_post(client, test_user, test_posts):
    res = client.post(
        "/posts/",
        json={"title": "başlık", "content": "içerik", "published": True},
    )
    assert res.status_code == 401


def test_unauthorized_user_delete_post(client, test_user, test_posts):
    res = client.delete(f"/posts/{test_posts[0].id}")
    assert res.status_code == 401


def test_delete_post_success(authorized_client, test_user, test_posts):
    res = authorized_client.delete(f"/posts/{test_posts[0].id}")
    assert res.status_code == 204


def test_delete_post_non_exist(authorized_client, test_user, test_posts):
    res = authorized_client.delete("/posts/8000000")
    assert res.status_code == 404


def test_delete_other_user_post(authorized_client, test_user, test_posts):
    res = authorized_client.delete(f"/posts/{test_posts[3].id}")
    assert res.status_code == 403


def test_update_post(authorized_client, test_user, test_posts):
    data = {
        "title": "güncellenmiş başlık",
        "content": "güncellenmiş içerik",
        "published": True,
    }
    res = authorized_client.put(f"/posts/{test_posts[0].id}", json=data)
    updated_post = schemas.PostResponse(**res.json())
    assert res.status_code == 200
    assert updated_post.title == data["title"]
    assert updated_post.content == data["content"]


def test_update_other_user_post(authorized_client, test_user, test_user2, test_posts):
    data = {
        "title": "güncellenmiş başlık",
        "content": "güncellenmiş içerik",
        "published": True,
    }
    res = authorized_client.put(f"/posts/{test_posts[3].id}", json=data)
    assert res.status_code == 403


def test_unauthorized_user_update_post(client, test_user, test_posts):
    res = client.put(f"/posts/{test_posts[0].id}")
    assert res.status_code == 401


def test_update_post_non_exist(authorized_client, test_user, test_posts):
    data = {
        "title": "güncellenmiş başlık",
        "content": "güncellenmiş içerik",
        "published": True,
    }
    res = authorized_client.put("/posts/8000000", json=data)
    assert res.status_code == 404
