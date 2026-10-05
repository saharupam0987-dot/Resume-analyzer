import os
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key-change-in-production-123456")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = plain_password.encode('utf-8')[:72]
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hash_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token_oauth: Optional[str] = Depends(oauth2_scheme),
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
) -> dict:
    token = token_oauth or (auth_header.credentials if auth_header else None)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please click the green 'Authorize' button in Swagger UI to log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        raw_sub = payload.get("sub")
        role: str = payload.get("role")
        email: Optional[str] = payload.get("email")
        if raw_sub is None or role is None:
            raise credentials_exception

        user_id = None
        if isinstance(raw_sub, int) or (isinstance(raw_sub, str) and raw_sub.isdigit()):
            user_id = int(raw_sub)
        elif payload.get("id") is not None:
            try:
                user_id = int(payload.get("id"))
            except (ValueError, TypeError):
                pass

        if user_id is None and ("@" in str(raw_sub) or email):
            from api.database import SessionLocal
            from api.models import Teacher, Student
            user_email = email or str(raw_sub)
            db_session = SessionLocal()
            try:
                if role == "teacher":
                    u = db_session.query(Teacher).filter(Teacher.email == user_email).first()
                else:
                    u = db_session.query(Student).filter(Student.email == user_email).first()
                if u:
                    user_id = u.id
                    email = u.email
            finally:
                db_session.close()

        if user_id is None:
            raise credentials_exception

        return {"id": user_id, "role": role, "email": email or str(raw_sub)}
    except (JWTError, ValueError):
        raise credentials_exception