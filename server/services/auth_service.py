from sqlalchemy.orm import Session

from core.security import verify_password
from crud.crud_auth import get_user_by_email
from models.User import User


def authenticate_user(db: Session, email: str, password: str) -> User | bool:
    """
    Validates email + password. Returns the User on success, False otherwise.
    Deliberately avoids leaking whether the email exists.
    """
    user = get_user_by_email(db, email)
    if not user:
        # Run verify anyway to avoid timing-based user enumeration
        verify_password(password, "$2b$12$placeholder_hash_to_prevent_timing_attack")
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user