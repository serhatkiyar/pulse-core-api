from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, oauth2, schemas, utils
from ..database import get_db


class AuthService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def login(self, user_credentials) -> schemas.Token:
        query = self.db.query(models.User).filter(
            models.User.email == user_credentials.username
        )
        user = query.first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Kullanıcı adı veya şifre yanlış",
            )

        if not utils.verify_password(user_credentials.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Kullanıcı adı veya şifre yanlış",
            )

        access_token = oauth2.create_token(data={"user_id": user.id})

        return schemas.Token(access_token=access_token, token_type="bearer")
