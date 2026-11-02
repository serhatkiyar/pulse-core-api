from fastapi import APIRouter, Depends, status

from ..schemas import UserCreate, UserResponse
from ..services.user_service import UserService

router = APIRouter(prefix="/users", tags=["User"])


@router.get("/{id}", response_model=UserResponse)
def get_user(id: int, user_service: UserService = Depends()):

    return user_service.get_by_id(user_id=id)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def create_user(user_in: UserCreate, user_service: UserService = Depends()):

    return user_service.create(user_in=user_in)
