from fastapi import Depends
from redis import asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models, utils
from ..database import get_db
from ..errors import EmailAlreadyExistsError, UserNotFoundError
from ..redis import get_redis
from ..schemas import UserCreate, UserResponse


class UserService:
    def __init__(
        self,
        redis: redis.Redis = Depends(get_redis),
        db: AsyncSession = Depends(get_db),
    ):
        self.db = db
        self.redis = redis

    async def get_by_id(self, user_id: int) -> UserResponse:
        cache_key = f"user:{user_id}"
        cached = await self.redis.get(cache_key)

        if cached:
            user_response = UserResponse.model_validate_json(cached)
            return user_response

        query = select(models.User).where(models.User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise UserNotFoundError

        user_response = UserResponse.model_validate(user)
        user_json = user_response.model_dump_json()

        await self.redis.set(cache_key, user_json, ex=60)
        return user_response

    async def create(
        self,
        user_in: UserCreate,
    ) -> UserResponse:

        query = select(models.User).where(models.User.email == user_in.email)
        result = await self.db.execute(query)
        user_exist = result.scalar_one_or_none()

        if user_exist:
            raise EmailAlreadyExistsError()

        user = models.User(**user_in.model_dump())
        user.password = utils.hash_password(user.password)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return UserResponse.model_validate(user)
