from datetime import UTC, datetime

from fastapi import Depends
from redis import asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models, oauth2, schemas, utils
from ..database import get_db
from ..errors import (
    InvalidUserCredentialsError,
    PermissionDeniedError,
)
from ..oauth2 import _decode_token
from ..redis import get_redis
from ..schemas import UserResponse


class AuthService:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        redis: redis.Redis = Depends(get_redis),
    ):
        self.db = db
        self.redis = redis

    async def login(self, user_credentials) -> schemas.Token:
        query = select(models.User).where(
            models.User.email == user_credentials.username
        )

        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise PermissionDeniedError()

        if not utils.verify_password(user_credentials.password, user.password):
            raise InvalidUserCredentialsError()

        await self.redis.set(
            f"user:{user.id}",
            UserResponse.model_validate(user).model_dump_json(),
            ex=600,
        )

        access_token = oauth2.create_token(data={"user_id": user.id})

        return schemas.Token(access_token=access_token, token_type="bearer")

    async def logout(self, token: str):
        payload = _decode_token(token)
        jti: str | None = payload.get("jti")
        if jti:
            exp: datetime | None = payload.get("exp")
            if exp:
                now = datetime.now(UTC).timestamp()
                exp_time = int(exp - now)
                if exp_time > 0:
                    cache_key = f"blacklist:{jti}"
                    await self.redis.set(cache_key, "1", ex=exp_time)
                    return {"message": "Çıkış yapıldı"}

        raise InvalidUserCredentialsError()
