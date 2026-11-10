import json

from fastapi import Depends
from redis import asyncio as redis

from .. import models
from ..errors import PermissionDeniedError, PostNotFoundError
from ..redis import get_redis
from ..repositories.post_repository import PostRepository
from ..schemas import PostCreate, PostDistanceResponse, PostResponse, PostUpdate
from .embedding_service import EmbeddingService


class PostService:
    def __init__(
        self,
        redis: redis.Redis = Depends(get_redis),
        embedding_service: EmbeddingService = Depends(EmbeddingService),
        post_repository: PostRepository = Depends(PostRepository),
    ):

        self.redis = redis
        self.embedding_service = embedding_service
        self.post_repository = post_repository

    async def _get_post_or_404(self, post_id: int) -> models.Post:
        post = await self.post_repository.get_by_id(post_id)

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

        posts = await self.post_repository.search_by_vector(
            query_embedding=query_embedding, limit=limit
        )

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

        vote_count = await self.post_repository.get_vote(post_id)

        await self.redis.set(cache_key, vote_count, ex=86400)
        return vote_count

    async def get_all(self, limit: int, skip: int, search: str) -> list[PostResponse]:
        cached_key = f"posts:limit={limit}:skip={skip}:search={search}"
        cached = await self.redis.get(cached_key)

        if cached:
            return [PostResponse.model_validate(i) for i in json.loads(cached)]

        posts = await self.post_repository.get_all(limit, skip, search)

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

        embedded = await self.embedding_service.get_embedding(
            f"{post.title}\n\n{post.content}"
        )
        post.embedding = embedded

        created_post = await self.post_repository.create(post)

        return PostResponse.model_validate(created_post)

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

        updated_post = await self.post_repository.update(post)

        return PostResponse.model_validate(updated_post)

    async def delete(self, post_id: int, user_id: int) -> None:
        post = await self._get_post_or_404(post_id)

        if post.owner_id != user_id:
            raise PermissionDeniedError()

        await self.post_repository.delete(post)

        await self.redis.delete(f"post:{post_id}", f"post:{post_id}:votes")
