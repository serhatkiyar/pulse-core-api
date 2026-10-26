import fastapi
from fastapi import Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, get_db

# ------------------ DATABASE BAĞLANTISI ----------------------
# for i in range(1, 6):
#     try:
#         conn = psycopg2.connect(
#             host=settings.DATABASE_HOST,
#             user=settings.DATABASE_USER,
#             database=settings.DATABASE_NAME,
#             password=settings.DATABASE_PASSWORD,
#             port=settings.DATABASE_PORT,
#             cursor_factory=RealDictCursor,
#         )
#         cursor = conn.cursor()
#         print("Bağlantı Başarılı")
#         break

#     except Exception as err:
#         print(f"Hata: {err}")
#         print(f"Bağlanma girişimi başarısız oldu ({i}/5)")
#         time.sleep(2)
# else:
#     print("Bağlanma girişimleri başarısız oldu")
#     sys.exit()
# ----------------------------------------------------------------

models.Base.metadata.create_all(bind=engine)

app = fastapi.FastAPI()


@app.get("/")
def root():
    return {"data": "Merhaba, Roottasın."}


@app.get("/posts")
def get_posts(db: Session = Depends(get_db)):

    posts = db.query(models.Post).all()

    # cursor.execute("SELECT * FROM posts")
    # posts = cursor.fetchall()

    return {"data": posts}


@app.get("/posts/{id}")
def get_post(id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == id).first()

    # cursor.execute("SELECT * FROM posts WHERE id = %s", (id,))
    # post = cursor.fetchone()

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{id} id'sine sahip post bulunamadı",
        )
    return {"data": post}


@app.post("/posts", status_code=status.HTTP_201_CREATED)
def add_post(post: schemas.Post, db: Session = Depends(get_db)):
    new_post = models.Post(**post.model_dump())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return {"data": new_post}

    # cursor.execute(
    #     "INSERT INTO posts (title, content, published) VALUES (%s, %s, %s) RETURNING *",
    #     (post.title, post.content, post.published),
    # )
    # new_post = cursor.fetchone()

    # conn.commit()
    return {"data": new_post}


@app.put("/posts/{id}")
def update_post(id: int, updated_post: schemas.Post, db: Session = Depends(get_db)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{id} id'sine sahip post bulunamadı",
        )

    post_query.update(updated_post.model_dump(), synchronize_session=False)
    db.commit()
    db.refresh(post)
    return {"data": post}
    # cursor.execute(
    #     "UPDATE posts SET title=%s, content=%s, published=%s WHERE id = %s RETURNING *",
    #     (
    #         updated_post.title,
    #         updated_post.content,
    #         updated_post.published,
    #         str(id),
    #     ),
    # )

    # updated_post = cursor.fetchone()

    # if updated_post is None:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"{id} id'sine sahip post bulunamadı",
    #     )

    # conn.commit()

    # return {"data": updated_post}


@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{id} id'sine sahip post bulunamadı",
        )
    post_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
    # cursor.execute("DELETE from posts WHERE id=%s RETURNING *", (str(id),))
    # deleted_post = cursor.fetchone()

    # if deleted_post is None:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"{id} id'sine sahip post bulunamadı",
    #     )

    # conn.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
