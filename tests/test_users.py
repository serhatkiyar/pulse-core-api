import pytest
from jose import jwt

from app import schemas
from app.config import settings


async def test_root(client):
    res = await client.get("/")
    assert res.json().get("message") == "Roottasın"
    assert res.status_code == 200


async def test_create_user(client):
    res = await client.post(
        "/users/",
        json={
            "name": "Serhat",
            "email": "serhat@gmail.com",
            "password": "password123",
        },
    )
    new_user = schemas.UserResponse(**res.json())
    assert new_user.email == "serhat@gmail.com"
    assert res.status_code == 201


async def test_login_user(client, test_user):
    res = await client.post(
        "/login",
        data={
            "username": test_user["email"],
            "password": test_user["password"],
        },
    )
    login_res = schemas.Token(**res.json())
    payload = jwt.decode(
        login_res.access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    id = payload.get("user_id")
    assert id == test_user["id"]
    assert login_res.token_type == "bearer"
    assert res.status_code == 200


@pytest.mark.parametrize(
    "email, password, status_code",
    [
        ("yanlis@gmail.com", "password123", 403),
        ("serhat@gmail.com", "yanlissifre", 403),
        ("yanlis@gmail.com", "yanlissifre", 403),
        (None, "password123", 422),
        ("serhat@gmail.com", None, 422),
    ],
)
async def test_incorrect_login(test_user, client, email, password, status_code):
    res = await client.post(
        "/login",
        data={"username": email, "password": password},
    )
    assert res.status_code == status_code


async def test_logout_and_blacklist(authorized_client):
    res = await authorized_client.post("/logout")
    assert res.status_code == 200
    assert res.json() == {"message": "Çıkış yapıldı"}

    res = await authorized_client.get("/posts/")
    assert res.status_code == 403
    assert res.json()["detail"] == "Bu oturum artık geçerli değil."


async def test_logout_twice_fails(authorized_client):
    res = await authorized_client.post("/logout")
    assert res.status_code == 200

    res = await authorized_client.post("/logout")
    assert res.status_code == 403
    assert res.json()["detail"] == "Bu oturum artık geçerli değil."


