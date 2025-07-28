from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

from ..database.database import get_db
from ..database.models import User, UserCRUD

# 환경 변수
SECRET_KEY = os.getenv("SECRET_KEY", "WeCanFarm_Auth_Key_Test")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# 패스워드 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 토큰 스키마
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """JWT 액세스 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """사용자 인증"""
    user = UserCRUD.get_by_username(db, username)
    if not user:
        user = UserCRUD.get_by_email(db, username)  # 이메일로도 로그인 가능
    
    if not user or not verify_password(password, user.password_hash):
        return None
    return user