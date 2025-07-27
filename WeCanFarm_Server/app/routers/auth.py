from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import jwt
from jwt import PyJWTError

from ..database.database import get_db
from ..database.models import UserCRUD, UserRole, User
from ..schemas.auth import UserRegister, UserLogin, Token
from ..auth.auth import (
    authenticate_user, 
    create_access_token, 
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,  # JWT 시크릿 키
    ALGORITHM   # JWT 알고리즘
)

router = APIRouter(prefix="/auth", tags=["authentication"])

# JWT 토큰 스키마
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    JWT 토큰에서 현재 사용자 정보를 가져오는 함수
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # JWT 토큰 디코딩
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except PyJWTError:
        raise credentials_exception
    
    # 사용자 ID로 DB에서 사용자 정보 조회
    try:
        user_id_int = int(user_id)
        user = UserCRUD.get_by_id(db, user_id_int)
        if user is None:
            raise credentials_exception
            
        # 비활성 사용자 체크
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="비활성화된 계정입니다"
            )
            
        return user
        
    except (ValueError, TypeError):
        raise credentials_exception
    except Exception as e:
        print(f"❌ 사용자 조회 실패: {e}")
        raise credentials_exception

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    활성 사용자만 가져오는 함수 (추가 검증)
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="비활성화된 사용자입니다"
        )
    return current_user

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    관리자 권한 사용자만 가져오는 함수
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user

@router.post("/register")
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """회원가입"""
    try:
        # 사용자명 중복 체크
        existing_user = UserCRUD.get_by_username(db, user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용 중인 사용자명입니다"
            )
        
        # 이메일 중복 체크
        existing_email = UserCRUD.get_by_email(db, user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용 중인 이메일입니다"
            )
        
        # 비밀번호 해싱
        hashed_password = get_password_hash(user_data.password)
        
        # 사용자 생성 (기본 USER 역할)
        new_user = UserCRUD.create(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            full_name=user_data.full_name,
            role=UserRole.USER
        )
        
        print(f"✅ 새 사용자 등록: {new_user.username} ({new_user.email})")
        
        return {"message": "회원가입이 완료되었습니다", "user_id": new_user.id}
        
    except HTTPException as he:
        raise he
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="사용자명 또는 이메일이 이미 사용 중입니다"
        )
    except Exception as e:
        db.rollback()
        print(f"❌ 회원가입 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원가입 처리 중 오류가 발생했습니다"
        )

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """로그인"""
    try:
        # 사용자 인증
        user = authenticate_user(db, user_credentials.username, user_credentials.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자명 또는 비밀번호가 올바르지 않습니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 비활성 사용자 체크
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="비활성화된 계정입니다"
            )
        
        # 액세스 토큰 생성
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, 
            expires_delta=access_token_expires
        )
        
        print(f"✅ 로그인 성공: {user.username}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            username=user.username
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ 로그인 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 처리 중 오류가 발생했습니다"
        )

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    현재 로그인한 사용자 정보 조회
    """
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    로그아웃 (클라이언트에서 토큰 삭제 지시)
    """
    print(f"✅ 로그아웃: {current_user.username}")
    return {"message": "로그아웃되었습니다"}

@router.post("/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """
    토큰 갱신
    """
    try:
        # 새로운 액세스 토큰 생성
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(current_user.id)}, 
            expires_delta=access_token_expires
        )
        
        print(f"✅ 토큰 갱신: {current_user.username}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=current_user.id,
            username=current_user.username
        )
        
    except Exception as e:
        print(f"❌ 토큰 갱신 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="토큰 갱신 중 오류가 발생했습니다"
        )