from fastapi import APIRouter, Depends, Request, Response, status

from .. import models
from ..limiter import limiter
from ..oauth2 import get_current_user
from ..schemas import PostCreate, PostResponse, PostUpdate
from ..services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get("/", response_model=list[PostResponse])
@limiter.limit("60/minute")
async def get_posts(
    request: Request,
    current_user: models.User = Depends(get_current_user),
    limit: int = 10,
    skip: int = 0,
    search: str | None = "",
    post_service: PostService = Depends(),
):
    return await post_service.get_all(limit=limit, skip=skip, search=search)


@router.get("/{id}", response_model=PostResponse)
@limiter.limit("60/minute")
async def get_post(
    request: Request,
    id: int,
    current_user: models.User = Depends(get_current_user),
    post_service: PostService = Depends(),
):
    return await post_service.get_by_id(post_id=id)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PostResponse)
@limiter.limit("20/minute")
async def add_post(
    request: Request,
    post_in: PostCreate,
    current_user: models.User = Depends(get_current_user),
    post_service: PostService = Depends(),
):
    return await post_service.create(post_in=post_in, user_id=current_user.id)


@router.put("/{id}", response_model=PostResponse)
@limiter.limit("20/minute")
async def update_post(
    request: Request,
    id: int,
    post_in: PostUpdate,
    current_user: models.User = Depends(get_current_user),
    post_service: PostService = Depends(),
):
    return await post_service.update(
        post_id=id, post_in=post_in, user_id=current_user.id
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def delete(
    request: Request,
    id: int,
    current_user: models.User = Depends(get_current_user),
    post_service: PostService = Depends(),
):
    await post_service.delete(post_id=id, user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id}/vote-count")
@limiter.limit("60/minute")
async def get_post_vote(
    request: Request,
    id: int,
    current_user: models.User = Depends(get_current_user),
    post_service: PostService = Depends(),
):
    vote_count = await post_service.get_post_votes(post_id=id)
    return {"post_id": id, "votes": vote_count}
