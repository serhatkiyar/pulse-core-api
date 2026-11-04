from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from .. import schemas
from ..limiter import limiter
from ..services.auth_service import AuthService

router = APIRouter(tags=["Auth"])


@router.post("/login", response_model=schemas.Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(),
):
    return await auth_service.login(user_credentials)
