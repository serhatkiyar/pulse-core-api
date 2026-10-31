from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, oauth2, schemas
from ..database import get_db

router = APIRouter(prefix="/vote", tags=["Vote"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def vote_post(
    vote_in: schemas.VoteIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    # 1. Postun var olup olmadığını kontrol et
    post = db.query(models.Post).filter(models.Post.id == vote_in.post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post bulunamadı"
        )

    # 2. Kullanıcının bu posta daha önce oy verip vermediğini kontrol et
    vote_query = db.query(models.Vote).filter(
        models.Vote.post_id == vote_in.post_id,
        models.Vote.user_id == current_user.id,
    )
    found_vote = vote_query.first()

    # 3. Oy verme işlemi (method == 1)
    if vote_in.method == 1:
        if found_vote:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{current_user.id} id'li kullanıcı bu postu zaten beğendi",
            )
        new_vote = models.Vote(post_id=vote_in.post_id, user_id=current_user.id)
        db.add(new_vote)
        db.commit()
        return {"message": "Post başarıyla beğenildi."}

    # 4. Beğeniyi geri çekme işlemi (method != 1, örn. 0)
    else:
        if not found_vote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Geri çekilecek bir beğeni bulunamadı",
            )
        vote_query.delete(synchronize_session=False)
        db.commit()
        return {"message": "Beğeni başarıyla geri çekildi."}
