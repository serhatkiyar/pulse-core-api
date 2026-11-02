from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from .. import schemas
from ..services.auth_service import AuthService

router = APIRouter(tags=["Auth"])


@router.post("/login", response_model=schemas.Token)
def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(),
):

    return auth_service.login(user_credentials)
