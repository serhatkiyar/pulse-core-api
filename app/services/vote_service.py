from fastapi import Depends
from redis import asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..database import get_db
from ..errors import PostAlreadyLikedError, VoteNotFoundError
from ..redis import get_redis
from ..schemas import VoteIn
from ..services.post_service import PostService


class VoteService:
    def __init__(
        self,
        redis: redis.Redis = Depends(get_redis),
        db: AsyncSession = Depends(get_db),
        post_service: PostService = Depends(),
    ):
        self.db = db
        self.post_service = post_service
        self.redis = redis

    async def vote(self, vote_in: VoteIn, user_id: int):
        await self.post_service.get_by_id(vote_in.post_id)

        query = select(models.Vote).where(
            models.Vote.post_id == vote_in.post_id, models.Vote.user_id == user_id
        )
        result = await self.db.execute(query)
        vote_found = result.scalar_one_or_none()

        cache_key = f"post:{vote_in.post_id}:votes"

        if vote_in.method == 1:
            if vote_found:
                raise PostAlreadyLikedError()
            new_vote = models.Vote(post_id=vote_in.post_id, user_id=user_id)
            self.db.add(new_vote)
            await self.db.commit()
            if await self.redis.exists(cache_key):
                await self.redis.incr(cache_key)

            return {"message": "Post başarıyla beğenildi."}

        else:
            if not vote_found:
                raise VoteNotFoundError()
            await self.db.delete(vote_found)
            await self.db.commit()
            if await self.redis.exists(cache_key):
                await self.redis.decr(cache_key)
            return {"message": "Beğeni başarıyla geri çekildi."}
