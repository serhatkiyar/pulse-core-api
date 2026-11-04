from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .. import models
from ..database import get_db
from ..errors import PermissionDeniedError, PostNotFoundError
from ..schemas import PostCreate, PostResponse, PostUpdate


class PostService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def _get_post_or_404(self, post_id: int) -> models.Post:
        query = (
            select(models.Post)
            .options(selectinload(models.Post.owner))
            .where(models.Post.id == post_id)
        )
        result = await self.db.execute(query)
        post = result.scalar_one_or_none()

        if not post:
            raise PostNotFoundError()
        return post

    async def get_all(self, limit: int, skip: int, search: str) -> list[PostResponse]:
        query = (
            select(models.Post)
            .options(selectinload(models.Post.owner))
            .where(models.Post.title.contains(search))
            .limit(limit)
            .offset(skip)
        )

        result = await self.db.execute(query)
        posts = result.scalars().all()

        return [PostResponse.model_validate(model) for model in posts]

    async def get_by_id(self, post_id: int) -> PostResponse:
        post = await self._get_post_or_404(post_id)
        return PostResponse.model_validate(post)

    async def create(self, post_in: PostCreate, user_id: int) -> PostResponse:
        post = models.Post(**post_in.model_dump(), owner_id=user_id)
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post, ["owner"])
        return PostResponse.model_validate(post)

    async def update(
        self, post_id: int, post_in: PostUpdate, user_id: int
    ) -> PostResponse:
        post = await self._get_post_or_404(post_id)

        if post.owner_id != user_id:
            raise PermissionDeniedError()

        for key, value in post_in.model_dump().items():
            setattr(post, key, value)

        await self.db.commit()
        await self.db.refresh(post, ["owner"])
        return PostResponse.model_validate(post)

    async def delete(self, post_id: int, user_id: int) -> None:
        post = await self._get_post_or_404(post_id)

        if post.owner_id != user_id:
            raise PermissionDeniedError()

        await self.db.delete(post)
        await self.db.commit()
