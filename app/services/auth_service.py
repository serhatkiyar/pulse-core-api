from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models, oauth2, schemas, utils
from ..database import get_db
from ..errors import InvalidUserCredentialsError, PermissionDeniedError


class AuthService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def login(self, user_credentials) -> schemas.Token:
        query = select(models.User).where(
            models.User.email == user_credentials.username
        )

        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise PermissionDeniedError()

        if not utils.verify_password(user_credentials.password, user.password):
            raise InvalidUserCredentialsError()

        access_token = oauth2.create_token(data={"user_id": user.id})

        return schemas.Token(access_token=access_token, token_type="bearer")
