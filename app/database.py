from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings

engine = create_engine(
    f"postgresql+psycopg2://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}/{settings.DATABASE_NAME}"
)

LocalSession = sessionmaker(autoflush=False, bind=engine)


def get_db():
    try:
        db = LocalSession()
        yield db
    finally:
        db.close()
