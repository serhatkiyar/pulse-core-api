from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..database import get_db
from ..errors import PostAlreadyLikedError, VoteNotFoundError
from ..schemas import VoteIn
from ..services.post_service import PostService


class VoteService:
    def __init__(
        self, db: AsyncSession = Depends(get_db), post_service: PostService = Depends()
    ):
        self.db = db
        self.post_service = post_service

    async def vote(self, vote_in: VoteIn, user_id: int):
        await self.post_service.get_by_id(vote_in.post_id)

        query = select(models.Vote).where(
            models.Vote.post_id == vote_in.post_id, models.Vote.user_id == user_id
        )
        result = await self.db.execute(query)
        vote_found = result.scalar_one_or_none()

        if vote_in.method == 1:
            if vote_found:
                raise PostAlreadyLikedError()
            new_vote = models.Vote(post_id=vote_in.post_id, user_id=user_id)
            self.db.add(new_vote)
            await self.db.commit()
            return {"message": "Post başarıyla beğenildi."}

        else:
            if not vote_found:
                raise VoteNotFoundError()
            # TODO: Oy'u sil
            await self.db.delete(vote_found)
            await self.db.commit()
            return {"message": "Beğeni başarıyla geri çekildi."}
