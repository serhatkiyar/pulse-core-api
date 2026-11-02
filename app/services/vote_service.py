from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..schemas import VoteIn
from ..services.post_service import PostService


class VoteService:
    def __init__(
        self, db: Session = Depends(get_db), post_service: PostService = Depends()
    ):
        self.db = db
        self.post_service = post_service

    def vote(self, vote_in: VoteIn, user_id: int):
        self.post_service.get_by_id(vote_in.post_id)

        vote_query = self.db.query(models.Vote).filter(
            models.Vote.post_id == vote_in.post_id,
            models.Vote.user_id == user_id,
        )
        found_vote = vote_query.first()

        if vote_in.method == 1:
            if found_vote:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"{user_id} id'li kullanıcı bu postu zaten beğendi",
                )
            new_vote = models.Vote(post_id=vote_in.post_id, user_id=user_id)
            self.db.add(new_vote)
            self.db.commit()
            return {"message": "Post başarıyla beğenildi."}

        else:
            if not found_vote:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Geri çekilecek bir beğeni bulunamadı",
                )
            vote_query.delete(synchronize_session=False)
            self.db.commit()
            return {"message": "Beğeni başarıyla geri çekildi."}
