from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..schemas import PostCreate, PostResponse, PostUpdate


class PostService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def _get_post_or_404(self, post_id: int) -> models.Post:
        query = self.db.query(models.Post).filter(models.Post.id == post_id)
        post = query.first()

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="post bulunamadı"
            )
        return post

    def get_all(self, limit: int, skip: int, search: str) -> list[PostResponse]:
        posts = (
            self.db.query(models.Post)
            .filter(models.Post.title.contains(search))
            .limit(limit)
            .offset(skip)
            .all()
        )
        return [PostResponse.model_validate(model) for model in posts]

    def get_by_id(self, post_id: int) -> PostResponse:
        post = self._get_post_or_404(post_id)
        return PostResponse.model_validate(post)

    def create(self, post_in: PostCreate, user_id: int) -> PostResponse:
        post = models.Post(**post_in.model_dump(), owner_id=user_id)
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return PostResponse.model_validate(post)

    def update(self, post_id: int, post_in: PostUpdate, user_id: int) -> PostResponse:
        post = self._get_post_or_404(post_id)

        if post.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu postu güncellemeye yetkiniz yok",
            )

        for key, value in post_in.model_dump().items():
            setattr(post, key, value)

        self.db.commit()
        self.db.refresh(post)
        return PostResponse.model_validate(post)

    def delete(self, post_id: int, user_id: int) -> None:
        post = self._get_post_or_404(post_id)

        if post.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu postu silmeye yetkiniz yok",
            )

        self.db.delete(post)
        self.db.commit()
