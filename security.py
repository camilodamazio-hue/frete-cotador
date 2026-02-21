from passlib.context import CryptContext
from fastapi import Request, Response
from itsdangerous import URLSafeSerializer, BadSignature
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def _serializer():
    secret = os.getenv("APP_SECRET", "dev-secret-change-me")
    return URLSafeSerializer(secret, salt="session")

COOKIE_NAME = "frete_session"

def set_session(response: Response, user_id: int):
    s = _serializer().dumps({"user_id": user_id})
    response.set_cookie(COOKIE_NAME, s, httponly=True, samesite="lax")

def clear_session(response: Response):
    response.delete_cookie(COOKIE_NAME)

def get_session_user_id(request: Request):
    raw = request.cookies.get(COOKIE_NAME)
    if not raw:
        return None
    try:
        data = _serializer().loads(raw)
        return int(data.get("user_id"))
    except (BadSignature, ValueError, TypeError):
        return None
