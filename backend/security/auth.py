from datetime import datetime, timedelta
from typing import Optional
import os
import base64
import hashlib
import hmac

from jose import JWTError, jwt

from backend.app.db import SessionLocal, PlatformUser

SECRET_KEY = "secureagent-super-secret-key-change-this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100_000,
    )
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    dk_b64 = base64.b64encode(dk).decode("utf-8")
    return f"{salt_b64}:{dk_b64}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt_b64, stored_hash_b64 = hashed_password.split(":")
        salt = base64.b64decode(salt_b64.encode("utf-8"))
        stored_hash = base64.b64decode(stored_hash_b64.encode("utf-8"))

        new_hash = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt,
            100_000,
        )

        return hmac.compare_digest(new_hash, stored_hash)
    except Exception:
        return False


def get_user_by_username(username: str) -> Optional[PlatformUser]:
    db = SessionLocal()
    try:
        return db.query(PlatformUser).filter(PlatformUser.username == username).first()
    finally:
        db.close()


def authenticate_user(username: str, password: str) -> Optional[PlatformUser]:
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def seed_default_users():
    db = SessionLocal()
    try:
        users = [
            ("admin", "admin123", "admin"),
            ("analyst", "analyst123", "analyst"),
            ("auditor", "auditor123", "auditor"),
        ]

        for username, password, role in users:
            existing = db.query(PlatformUser).filter(PlatformUser.username == username).first()
            if not existing:
                db.add(
                    PlatformUser(
                        username=username,
                        hashed_password=hash_password(password),
                        role=role,
                    )
                )

        db.commit()
    finally:
        db.close()