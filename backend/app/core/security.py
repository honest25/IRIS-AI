from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from jose import jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import base64
import hashlib

from app.core.config import settings

# ─── Password Hashing ────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ─── JWT Tokens ──────────────────────────────────────────────────────────────
def create_access_token(
    subject: Union[str, int],
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: Union[str, int]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token. Returns payload or None."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except Exception:
        return None


def verify_refresh_token(token: str) -> Optional[str]:
    """Returns user_id (sub) string if refresh token is valid, else None."""
    payload = decode_token(token)
    if payload and payload.get("type") == "refresh":
        return payload.get("sub")
    return None


# ─── Fernet Symmetric Encryption ─────────────────────────────────────────────
def _get_fernet() -> Fernet:
    """Build a Fernet instance from the ENCRYPTION_KEY setting."""
    key = settings.ENCRYPTION_KEY
    if not key:
        # Derive a stable key from SECRET_KEY so the app works without explicit config
        derived = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(derived).decode()
    # Ensure proper Fernet key format (32 url-safe base64 bytes)
    key_bytes = key.encode() if isinstance(key, str) else key
    return Fernet(key_bytes)


def encrypt_data(data: str) -> str:
    """Encrypt a plaintext string, returns URL-safe base64 ciphertext."""
    f = _get_fernet()
    return f.encrypt(data.encode()).decode()


def decrypt_data(token: str) -> str:
    """Decrypt a Fernet-encrypted string back to plaintext."""
    f = _get_fernet()
    return f.decrypt(token.encode()).decode()
