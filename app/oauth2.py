import uuid
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from redis import asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import models
from .config import settings
from .database import get_db
from .errors import SessionExpiredError
from .redis import get_redis
from .schemas import TokenData, UserResponse

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def _decode_token(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload


def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
    encoded_jwt = jwt.encode(to_encode, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_access_token(
    token: str, credentials_exception, redis: redis.Redis
) -> TokenData:
    try:
        payload = jwt.decode(token=token, key=SECRET_KEY, algorithms=[ALGORITHM])
        id: str | None = payload.get("user_id")
        jti: str | None = payload.get("jti")
        if not id or not jti:
            raise credentials_exception

        cache_key = f"blacklist:{jti}"
        cached = await redis.get(cache_key)
        if cached:
            raise SessionExpiredError()

        token_data = TokenData(id=str(id))
    except JWTError:
        raise credentials_exception

    return token_data


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis: redis.Redis = Depends(get_redis),
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = await verify_access_token(token, credentials_exception, redis)

    user_cache_key = f"user:{token_data.id}"
    cached_user = await redis.get(user_cache_key)

    if cached_user:
        return UserResponse.model_validate_json(cached_user)

    query = select(models.User).where(models.User.id == int(token_data.id))
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise credentials_exception

    user_response = UserResponse.model_validate(user)
    await redis.set(user_cache_key, user_response.model_dump_json(), ex=600)

    return user
