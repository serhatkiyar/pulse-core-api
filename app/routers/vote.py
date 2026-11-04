from fastapi import APIRouter, Depends, Request, status

from .. import oauth2, schemas
from ..limiter import limiter
from ..models import User
from ..services.vote_service import VoteService

router = APIRouter(prefix="/vote", tags=["Vote"])


@router.post("/", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def vote_post(
    request: Request,
    vote_in: schemas.VoteIn,
    current_user: User = Depends(oauth2.get_current_user),
    vote_service: VoteService = Depends(),
):
    return await vote_service.vote(vote_in=vote_in, user_id=current_user.id)
