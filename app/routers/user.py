from fastapi import APIRouter, BackgroundTasks, Depends, Request, status

from .. import models
from ..limiter import limiter
from ..oauth2 import RoleChecker
from ..schemas import UserCreate, UserResponse
from ..services.email_service import send_welcome_email
from ..services.user_service import UserService

router = APIRouter(prefix="/users", tags=["User"])


@router.get("/{id}", response_model=UserResponse)
async def get_user(id: int, user_service: UserService = Depends()):
    return await user_service.get_by_id(user_id=id)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
@limiter.limit("10/minute")
async def create_user(
    request: Request,
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    user_service: UserService = Depends(),
):
    user = await user_service.create(user_in=user_in)
    background_tasks.add_task(send_welcome_email, to_email=user.email, name=user.name)
    return user


@router.get("/", response_model=list[UserResponse])
@limiter.limit("10/minute")
async def get_all_users(
    request: Request,
    user_service: UserService = Depends(),
    user_credentials: models.User = Depends(RoleChecker([models.Roles.ADMIN])),
    limit: int = 10,
):
    return await user_service.get_all(limit)
