from pydantic import BaseModel, EmailStr, validator
from typing import Optional

class UserRegister(BaseModel):
    """회원가입 요청"""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if len(v) < 3 or len(v) > 20:
            raise ValueError('사용자명은 3~20자 사이여야 합니다')
        if not v.isalnum():
            raise ValueError('사용자명은 영문과 숫자만 사용 가능합니다')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('비밀번호는 최소 6자 이상이어야 합니다')
        return v

class UserLogin(BaseModel):
    """로그인 요청"""
    username: str  # username 또는 email
    password: str

class Token(BaseModel):
    """토큰 응답"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str