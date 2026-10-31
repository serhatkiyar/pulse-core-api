from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, utils
from ..database import get_db
from ..schemas import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["User"])


@router.get("/{id}", response_model=UserResponse)
def get_user(id: int, db: Session = Depends(get_db)):
    query = db.query(models.User).filter(models.User.id == id)
    user = query.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Kullanıcı bulunamadı."
        )
    return user


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    user = models.User(**user_in.model_dump())
    user.password = utils.hash_password(user.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
