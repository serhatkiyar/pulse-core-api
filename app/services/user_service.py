from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, utils
from ..database import get_db
from ..schemas import UserCreate, UserResponse


class UserService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get_by_id(self, user_id: int) -> UserResponse:
        query = self.db.query(models.User).filter(models.User.id == user_id)
        user = query.first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Kullanıcı bulunamadı."
            )

        return UserResponse.model_validate(user)

    def create(
        self,
        user_in: UserCreate,
    ) -> UserResponse:

        existing_user = (
            self.db.query(models.User)
            .filter(models.User.email == user_in.email)
            .first()
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bu e-posta adresiyle kayıtlı bir kullanıcı zaten mevcut.",
            )

        user = models.User(**user_in.model_dump())
        user.password = utils.hash_password(user.password)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return UserResponse.model_validate(user)
