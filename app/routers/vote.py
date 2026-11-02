from fastapi import APIRouter, Depends, status

from .. import models, oauth2, schemas
from ..services.vote_service import VoteService

router = APIRouter(prefix="/vote", tags=["Vote"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def vote_post(
    vote_in: schemas.VoteIn,
    current_user: models.User = Depends(oauth2.get_current_user),
    vote_service: VoteService = Depends(),
):
    return vote_service.vote(vote_in=vote_in, user_id=current_user.id)
