from fastapi import Depends
from redis import asyncio as redis

from .. import models, utils
from ..errors import EmailAlreadyExistsError, UserNotFoundError
from ..redis import get_redis
from ..repositories.user_repository import UserRepository
from ..schemas import UserCreate, UserResponse


class UserService:
    def __init__(
        self,
        redis: redis.Redis = Depends(get_redis),
        user_repository: UserRepository = Depends(UserRepository),
    ):
        self.redis = redis
        self.user_repository = user_repository

    async def get_by_id(self, user_id: int) -> UserResponse:
        cache_key = f"user:{user_id}"
        cached = await self.redis.get(cache_key)

        if cached:
            user_response = UserResponse.model_validate_json(cached)
            return user_response

        user = await self.user_repository.get_by_id(user_id)

        if not user:
            raise UserNotFoundError

        user_response = UserResponse.model_validate(user)
        user_json = user_response.model_dump_json()

        await self.redis.set(cache_key, user_json, ex=60)
        return user_response

    async def get_all(self, limit=10) -> list[UserResponse]:
        users = await self.user_repository.get_all(limit)
        return [UserResponse.model_validate(user) for user in users]

    async def create(
        self,
        user_in: UserCreate,
    ) -> UserResponse:

        user_exist = await self.user_repository.isUser(user_in.email)

        if user_exist:
            raise EmailAlreadyExistsError()

        user = models.User(**user_in.model_dump())
        user.password = utils.hash_password(user.password)

        created_user = await self.user_repository.create(user)
        return UserResponse.model_validate(created_user)
