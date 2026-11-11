from fastapi import Depends
from redis import asyncio as redis

from .. import models
from ..errors import PostAlreadyLikedError, VoteNotFoundError
from ..redis import get_redis
from ..repositories.vote_repository import VoteRepository
from ..schemas import VoteIn
from ..services.post_service import PostService


class VoteService:
    def __init__(
        self,
        redis: redis.Redis = Depends(get_redis),
        post_service: PostService = Depends(),
        vote_repository: VoteRepository = Depends(VoteRepository),
    ):
        self.post_service = post_service
        self.redis = redis
        self.vote_repository = vote_repository

    async def vote(self, vote_in: VoteIn, user_id: int):
        await self.post_service.get_by_id(vote_in.post_id)

        vote_found = await self.vote_repository.get(
            vote_in.post_id, user_id, for_update=True
        )
        cache_key = f"post:{vote_in.post_id}:votes"

        if vote_in.method == 1:
            if vote_found:
                raise PostAlreadyLikedError()

            new_vote = models.Vote(post_id=vote_in.post_id, user_id=user_id)
            await self.vote_repository.create(new_vote)

            if await self.redis.exists(cache_key):
                await self.redis.incr(cache_key)

            return {"message": "Post başarıyla beğenildi."}

        else:
            if not vote_found:
                raise VoteNotFoundError()

            await self.vote_repository.delete(vote_found)

            if await self.redis.exists(cache_key):
                await self.redis.decr(cache_key)
            return {"message": "Beğeni başarıyla geri çekildi."}
