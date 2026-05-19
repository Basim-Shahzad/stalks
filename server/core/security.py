from datetime import datetime, timedelta, UTC
import secrets
import jwt
from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordBearer
from core.config import settings

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, settings.secret_key.get_secret_value(), algorithm=settings.algorithm
    )


def create_refresh_token() -> tuple[str, datetime]:
    """
    Returns a (token_string, expiry_datetime) tuple.
    The token is a cryptographically secure random hex string — NOT a JWT.
    It is stored hashed in the DB and only the raw value is returned to the client.
    """
    token = secrets.token_hex(64)
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    return token, expires_at
