from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from .. import models, schemas
from ..limiter import limiter
from ..oauth2 import get_current_user, oauth2_scheme
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


@router.post("/logout")
@limiter.limit("5/minute")
async def logout(
    request: Request,
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(),
    user_credentials: models.User = Depends(get_current_user),
):
    await auth_service.logout(token)
    return {"message": "Çıkış yapıldı"}
