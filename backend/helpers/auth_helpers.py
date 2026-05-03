import bcrypt
import re
from datetime import datetime, timezone
from app.models import TokenBlocklist
from app import db

def validate_email(email: str) -> bool:
    """_summary_

    Args:
        email (str): _description_

    Returns:
        bool: _description_
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))

def validate_password(password: str) -> bool:
    """_summary_

    Args:
        password (str): _description_

    Returns:
        bool: _description_
    """
    return len(password) >= 8

def hash_password(password: str) -> str:
    """_summary_

    Args:
        password (str): _description_

    Returns:
        str: _description_
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """_summary_

    Args:
        password (str): _description_
        hashed_password (str): _description_

    Returns:
        bool: _description_
    """
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def _blocklist_jti(jti: str) -> None:
    """Persist a JTI to the blocklist table."""
    entry = TokenBlocklist(jti=jti, created_at=datetime.now(timezone.utc))
    db.session.add(entry)
    db.session.commit()
    