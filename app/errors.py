class AppException(Exception): ...


class NotFoundError(AppException): ...


class ConflictError(AppException): ...


class AuthenticationError(AppException): ...


class AuthorizationError(AppException): ...


class PostNotFoundError(NotFoundError):
    def __init__(self, post_id: int | None = None):
        super().__init__(f"{post_id} id'li Post bulunamadı.")
        self.status_code = 404


class UserNotFoundError(NotFoundError):
    def __init__(self, user_id: int | None = None):
        super().__init__(f"{user_id} id'li Kullanıcı bulunamadı.")
        self.status_code = 404


class VoteNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__("Bu postta beğeniniz bulunmuyor.")
        self.status_code = 404


class PermissionDeniedError(AuthorizationError):
    def __init__(self):
        super().__init__("Bu işlemi yapmak için yetkiniz yok.")
        self.status_code = 403


class InvalidUserCredentialsError(AuthenticationError):
    def __init__(self):
        super().__init__("Kullanıcı adı veya Şifre yanlış.")
        self.status_code = 403


class SessionExpiredError(AuthenticationError):
    def __init__(self):
        super().__init__("Bu oturum artık geçerli değil.")
        self.status_code = 403


class EmailAlreadyExistsError(ConflictError):
    def __init__(self, email: str | None = None):
        super().__init__(f"{email} maili zaten sistemde kayıtlı.")
        self.status_code = 409


class PostAlreadyLikedError(ConflictError):
    def __init__(self):
        super().__init__("Bu post zaten beğenildi.")
        self.status_code = 409
