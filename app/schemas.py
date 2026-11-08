from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PostBase(BaseModel):
    title: str
    content: str
    published: bool


class PostCreate(PostBase):
    pass


class PostUpdate(PostCreate):
    pass


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenData(BaseModel):
    id: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str


class VoteIn(BaseModel):
    post_id: int
    # 1: beğen, 0: beğeniyi geri çek
    method: Literal[0, 1]


class PostResponse(PostBase):
    id: int
    created_at: datetime
    owner_id: int
    owner: UserResponse

    model_config = ConfigDict(from_attributes=True)


class PostDistanceResponse(PostResponse):
    distance: float


class RAGRequest(BaseModel):
    question: str
    limit: int = 5


class RAGResponse(BaseModel):
    thought_process: list[str] = Field(
        description="Soruyu yanıtlarken bağlamdaki hangi bilgileri nasıl değerlendirdiğinin adım adım kısa düşüncesi"
    )
    answer: str = Field(
        description="Kullanıcının sorusuna yalnızca verilen bağlam (postlar) kullanılarak verilen net Türkçe yanıt"
    )
    enough_context: bool = Field(
        description="Verilen postlardaki bilgileri soruyu doğru yanıtlamak için yeterli miydi?"
    )
    source_post_ids: list[int] = Field(
        description="Yanıtı oluştururken doğrudan kullanılan postların ID listesi (hiçbiri kullanılmadıysa boş liste)"
    )
