from datetime import UTC, datetime

from fastapi import Depends, HTTPException, status
from redis import asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models, oauth2, schemas, utils
from ..config import settings
from ..database import get_db
from ..errors import (
    InvalidUserCredentialsError,
    PermissionDeniedError,
)
from ..oauth2 import _decode_token
from ..redis import get_redis
from ..schemas import UserResponse


class AuthService:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        redis: redis.Redis = Depends(get_redis),
    ):
        self.db = db
        self.redis = redis

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

        await self.redis.set(
            f"user:{user.id}",
            UserResponse.model_validate(user).model_dump_json(),
            ex=600,
        )

        access_token = oauth2.create_access_token(
            data={"user_id": user.id, "role": user.role}
        )
        refresh_token = oauth2.create_refresh_token(
            data={"user_id": user.id}
        )

        return schemas.Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_tokens(self, refresh_token_str: str) -> schemas.Token:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        payload = oauth2.verify_refresh_token(refresh_token_str, credentials_exception)
        user_id = payload["user_id"]
        jti = payload["jti"]
        iat = payload.get("iat", 0)

        # 1. Kullanıcının tüm oturumları kapatılmış mı?
        revoked_at = await self.redis.get(f"user:{user_id}:revoked_at")
        if revoked_at and iat <= int(revoked_at):
            raise credentials_exception

        # 2. Token Reuse Detection (Çift Kullanım / Hırsızlık Kontrolü):
        is_used = await self.redis.get(f"used_refresh:{jti}")
        if is_used:
            now_ts = int(datetime.now(UTC).timestamp())
            await self.redis.set(
                f"user:{user_id}:revoked_at",
                str(now_ts),
                ex=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Güvenlik ihlali tespit edildi. Tüm oturumlar kapatıldı.",
            )

        # 3. Meşru kullanım: Eski refresh token'ı kullanılmış olarak işaretle
        exp = payload.get("exp")
        now = datetime.now(UTC).timestamp()
        remaining_ttl = (
            int(exp - now) if exp else settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        )
        if remaining_ttl > 0:
            await self.redis.set(f"used_refresh:{jti}", "1", ex=remaining_ttl)

        # 4. Kullanıcıyı getir
        query = select(models.User).where(models.User.id == int(user_id))
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise credentials_exception

        # 5. Yeni token çifti üret (Rotation)
        new_access_token = oauth2.create_access_token(
            data={"user_id": user.id, "role": user.role}
        )
        new_refresh_token = oauth2.create_refresh_token(
            data={"user_id": user.id}
        )

        return schemas.Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def logout(self, token: str):
        payload = _decode_token(token)
        jti: str | None = payload.get("jti")
        if jti:
            exp: datetime | None = payload.get("exp")
            if exp:
                now = datetime.now(UTC).timestamp()
                exp_time = int(exp - now)
                if exp_time > 0:
                    cache_key = f"blacklist:{jti}"
                    await self.redis.set(cache_key, "1", ex=exp_time)
                    return {"message": "Çıkış yapıldı"}

        raise InvalidUserCredentialsError()
