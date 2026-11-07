import json

from fastapi import Depends
from redis import asyncio as redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .. import models
from ..database import get_db
from ..errors import PermissionDeniedError, PostNotFoundError
from ..redis import get_redis
from ..schemas import PostCreate, PostDistanceResponse, PostResponse, PostUpdate
from .embedding_service import EmbeddingService


class PostService:
    def __init__(
        self,
        redis: redis.Redis = Depends(get_redis),
        db: AsyncSession = Depends(get_db),
        embedding_service: EmbeddingService = Depends(EmbeddingService),
    ):

        self.db = db
        self.redis = redis
        self.embedding_service = embedding_service

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

    async def semantic_search(
        self, query_text: str, limit: int = 5
    ) -> list[PostResponse]:
        query_embedding = await self.embedding_service.get_embedding(
            text=query_text,
            task_type="RETRIEVAL_QUERY",
        )

        distance_col = models.Post.embedding.cosine_distance(query_embedding).label(
            "distance"
        )
        MAX_DISTANCE = 0.45

        query = (
            select(models.Post, distance_col)
            .options(selectinload(models.Post.owner))
            .where(models.Post.embedding.is_not(None))
            .where(distance_col < MAX_DISTANCE)
            .order_by(models.Post.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )

        result = await self.db.execute(query)
        posts = result.all()
        return [
            PostDistanceResponse(
                **PostResponse.model_validate(post).model_dump(), distance=distance
            )
            for post, distance in posts
        ]

    async def get_post_votes(self, post_id: int) -> int:
        await self._get_post_or_404(post_id)

        cache_key = f"post:{post_id}:votes"
        cached = await self.redis.get(cache_key)

        if cached is not None:
            return int(cached)

        query = (
            select(func.count())
            .select_from(models.Vote)
            .where(models.Vote.post_id == post_id)
        )
        result = await self.db.execute(query)
        vote_count = result.scalar() or 0

        await self.redis.set(cache_key, vote_count, ex=86400)
        return vote_count

    async def get_all(self, limit: int, skip: int, search: str) -> list[PostResponse]:
        cached_key = f"posts:limit={limit}:skip={skip}:search={search}"
        cached = await self.redis.get(cached_key)

        if cached:
            return [PostResponse.model_validate(i) for i in json.loads(cached)]

        query = (
            select(models.Post)
            .options(selectinload(models.Post.owner))
            .where(models.Post.title.contains(search))
            .limit(limit)
            .offset(skip)
        )

        result = await self.db.execute(query)
        posts = result.scalars().all()

        posts_response = [
            PostResponse.model_validate(i).model_dump(mode="json") for i in posts
        ]
        await self.redis.set(cached_key, json.dumps(posts_response), ex=5)

        return posts_response

    async def get_by_id(self, post_id: int) -> PostResponse:
        cache_key = f"post:{post_id}"
        cached = await self.redis.get(cache_key)

        if cached:
            return PostResponse.model_validate_json(cached)

        post = await self._get_post_or_404(post_id)
        post_response = PostResponse.model_validate(post)
        await self.redis.set(cache_key, post_response.model_dump_json(), ex=60)

        return PostResponse.model_validate(post)

    async def create(self, post_in: PostCreate, user_id: int) -> PostResponse:
        post = models.Post(**post_in.model_dump(), owner_id=user_id)
        self.db.add(post)

        embedded = await self.embedding_service.get_embedding(
            f"{post.title}\n\n{post.content}"
        )
        post.embedding = embedded
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

        embedded = await self.embedding_service.get_embedding(
            f"{post.title}\n\n{post.content}"
        )
        post.embedding = embedded

        await self.db.commit()

        await self.redis.delete(f"post:{post_id}")
        await self.db.refresh(post, ["owner"])
        return PostResponse.model_validate(post)

    async def delete(self, post_id: int, user_id: int) -> None:
        post = await self._get_post_or_404(post_id)

        if post.owner_id != user_id:
            raise PermissionDeniedError()

        await self.db.delete(post)
        await self.db.commit()
        await self.redis.delete(f"post:{post_id}", f"post:{post_id}:votes")
