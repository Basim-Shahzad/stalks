from sqlalchemy.orm import Session
from sqlalchemy import select
from uuid import UUID
from datetime import datetime

from models.User import User
from models.RefreshToken import RefreshToken
from schemas.UserSchema import UserCreateSchema, UserUpdateSchema
from core.security import hash_password


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------

def get_user_by_email(db: Session, email: str) -> User | None:
    """Fetch a single user by their email address."""
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    """Fetch a single user by their UUID."""
    return db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()


def create_user(db: Session, user_in: UserCreateSchema) -> User:
    """Creates a new user in the database."""
    user_data = user_in.model_dump(exclude={"password"})
    db_user = User(**user_data)
    db_user.password_hash = hash_password(user_in.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, db_user: User, user_in: UserUpdateSchema) -> User:
    """Updates an existing user's attributes."""
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        db_user.password_hash = hash_password(update_data.pop("password"))
    for field, value in update_data.items():
        setattr(db_user, field, value)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: UUID) -> bool:
    """Hard-deletes a user. Returns True if deleted, False if not found."""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True


def deactivate_user(db: Session, db_user: User) -> User:
    """Sets is_active to False instead of a hard delete."""
    db_user.is_active = False
    db.commit()
    db.refresh(db_user)
    return db_user


# ---------------------------------------------------------------------------
# Refresh token CRUD
# ---------------------------------------------------------------------------

def create_refresh_token_record(
    db: Session, user_id: UUID, token: str, expires_at: datetime
) -> RefreshToken:
    """Persist a new refresh token record for a user."""
    db_token = RefreshToken(user_id=user_id, token=token, expires_at=expires_at)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def get_refresh_token(db: Session, token: str) -> RefreshToken | None:
    """Look up a refresh token record by its raw token value."""
    return db.execute(
        select(RefreshToken).where(RefreshToken.token == token)
    ).scalar_one_or_none()


def revoke_refresh_token(db: Session, db_token: RefreshToken) -> None:
    """Mark a single refresh token as revoked."""
    db_token.revoked = True
    db.commit()


def revoke_all_user_refresh_tokens(db: Session, user_id: UUID) -> None:
    """Revoke every active refresh token for a user (logout-all-devices)."""
    tokens = db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked.is_(False),
        )
    ).scalars().all()
    for t in tokens:
        t.revoked = True
    db.commit()