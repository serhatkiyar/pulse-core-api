from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Vote


class VoteRepository:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def get(self, post_id: int, user_id: int) -> Vote | None:
        query = select(Vote).where(Vote.post_id == post_id, Vote.user_id == user_id)
        result = await self.db.execute(query)
        vote = result.scalar_one_or_none()

        return vote

    async def create(self, vote: Vote) -> Vote:
        self.db.add(vote)
        await self.db.commit()
        return vote

    async def delete(self, vote: Vote) -> None:
        await self.db.delete(vote)
        await self.db.commit()
