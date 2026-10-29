import bcrypt
from passlib.context import CryptContext

# Passlib 1.7.4 compatibility with bcrypt >= 4.0.0
if not hasattr(bcrypt, "__about__"):

    class About:
        __version__ = getattr(bcrypt, "__version__", "4.0.0")

    bcrypt.__about__ = About()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash(password: str) -> str:
    return pwd_context.hash(password)


def verify(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
