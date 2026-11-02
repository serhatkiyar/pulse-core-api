from fastapi import APIRouter, Depends, Response, status

from .. import models
from ..oauth2 import get_current_user
from ..schemas import PostCreate, PostResponse, PostUpdate
from ..services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get("/", response_model=list[PostResponse])
def get_posts(
    current_user: models.User = Depends(get_current_user),
    limit: int = 10,
    skip: int = 0,
    search: str | None = "",
    post_service: PostService = Depends(),
):

    return post_service.get_all(limit=limit, skip=skip, search=search)


@router.get("/{id}", response_model=PostResponse)
def get_post(
    id: int,
    current_user: models.User = Depends(get_current_user),
    post_service: PostService = Depends(),
):

    return post_service.get_by_id(post_id=id)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PostResponse)
def add_post(
    post_in: PostCreate,
    current_user: models.User = Depends(get_current_user),
    post_service: PostService = Depends(),
):

    return post_service.create(post_in=post_in, user_id=current_user.id)


@router.put("/{id}", response_model=PostResponse)
def update_post(
    id: int,
    post_in: PostUpdate,
    current_user: models.User = Depends(get_current_user),
    post_service: PostService = Depends(),
):

    return post_service.update(post_id=id, post_in=post_in, user_id=current_user.id)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    id: int,
    current_user: models.User = Depends(get_current_user),
    post_service: PostService = Depends(),
):

    post_service.delete(post_id=id, user_id=current_user.id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
