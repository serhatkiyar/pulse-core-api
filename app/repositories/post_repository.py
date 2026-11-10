from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import Post, Vote


class PostRepository:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def get_by_id(self, post_id: int):
        query = select(Post).options(selectinload(Post.owner)).where(Post.id == post_id)
        result = await self.db.execute(query)
        post = result.scalar_one_or_none()

        return post

    async def get_all(self, limit: int, skip: int, search: str):
        query = (
            select(Post)
            .options(selectinload(Post.owner))
            .where(Post.title.contains(search))
            .limit(limit)
            .offset(skip)
        )
        result = await self.db.execute(query)
        posts = result.scalars().all()

        return posts

    async def get_vote(self, post_id: int):
        query = select(func.count()).select_from(Vote).where(Vote.post_id == post_id)

        result = await self.db.execute(query)
        vote = result.scalar() or 0
        return vote

    async def create(self, post: Post):
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post, ["owner"])
        return post

    async def update(self, post: Post):
        await self.db.commit()
        await self.db.refresh(post, ["owner"])
        return post

    async def delete(self, post: Post) -> None:
        await self.db.delete(post)
        await self.db.commit()

    async def search_by_vector(
        self, query_embedding: list[float], limit: int = 5, max_distance: float = 0.45
    ):
        distance_col = Post.embedding.cosine_distance(query_embedding).label("distance")

        query = (
            select(Post, distance_col)
            .options(selectinload(Post.owner))
            .where(Post.embedding.is_not(None))
            .where(distance_col < max_distance)
            .order_by(Post.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return result.all()
