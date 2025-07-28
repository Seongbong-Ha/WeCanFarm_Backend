from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import jwt
from jwt import PyJWTError

from ..database.database import get_db
from ..database.models import UserCRUD, UserRole, User
from ..schemas.auth import UserRegister, UserLogin, Token, RegisterUserRole, RegisterResponse
from ..auth.auth import (
    authenticate_user, 
    create_access_token, 
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    ALGORITHM
)

router = APIRouter(prefix="/auth", tags=["authentication"])

# JWT 토큰 스키마
security = HTTPBearer()

# app/routers/auth.py의 get_current_user 함수를 다음과 같이 수정

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """JWT 토큰에서 현재 사용자 정보를 가져오는 함수 - 완전 디버깅 버전"""
    
    print("🚨 === GET_CURRENT_USER 디버깅 시작 ===")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        print(f"🔍 step 1: credentials 확인")
        print(f"   - credentials: {credentials}")
        print(f"   - credentials.credentials: {credentials.credentials[:50] if credentials and credentials.credentials else 'NONE'}...")
        
        if not credentials or not credentials.credentials:
            print("❌ step 1: credentials가 없음")
            raise credentials_exception
        
        print(f"🔍 step 2: JWT 디코딩 시도")
        # SECRET_KEY와 ALGORITHM import
        from ..auth.auth import SECRET_KEY, ALGORITHM
        print(f"   - SECRET_KEY 길이: {len(SECRET_KEY)}")
        print(f"   - ALGORITHM: {ALGORITHM}")
        
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"✅ step 2: JWT 디코딩 성공")
        print(f"   - payload: {payload}")
        
        user_id: str = payload.get("sub")
        if user_id is None:
            print("❌ step 2: user_id가 payload에 없음")
            raise credentials_exception
            
        print(f"🔍 step 3: 사용자 조회 시도")
        print(f"   - user_id: {user_id}")
        
    except PyJWTError as e:
        print(f"❌ step 2: JWT 디코딩 실패 - {type(e).__name__}: {e}")
        raise credentials_exception
    except Exception as e:
        print(f"❌ step 2: 예상치 못한 디코딩 에러 - {type(e).__name__}: {e}")
        raise credentials_exception
    
    try:
        user_id_int = int(user_id)
        print(f"   - user_id_int: {user_id_int}")
        
        user = UserCRUD.get_by_id(db, user_id_int)
        if user is None:
            print(f"❌ step 3: 사용자 없음 (ID: {user_id_int})")
            raise credentials_exception
            
        print(f"✅ step 3: 사용자 발견")
        print(f"   - username: {user.username}")
        print(f"   - is_active: {user.is_active}")
            
        if not user.is_active:
            print(f"❌ step 4: 비활성 사용자")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="비활성화된 계정입니다"
            )
            
        print(f"✅ === GET_CURRENT_USER 완료: {user.username} ===")
        return user
        
    except (ValueError, TypeError) as e:
        print(f"❌ step 3: user_id 변환 실패 - {e}")
        raise credentials_exception
    except HTTPException as he:
        print(f"❌ step 4: HTTP 예외 - {he.detail}")
        raise he
    except Exception as e:
        print(f"❌ step 3: DB 조회 실패 - {type(e).__name__}: {e}")
        import traceback
        print(f"   스택트레이스: {traceback.format_exc()}")
        raise credentials_exception

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """활성 사용자만 가져오는 함수"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="비활성화된 사용자입니다"
        )
    return current_user

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """관리자 권한 사용자만 가져오는 함수"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user

@router.post("/register", response_model=RegisterResponse)
async def register(request: Request, user_data: UserRegister, db: Session = Depends(get_db)):
    """회원가입 - 역할 선택 포함"""
    
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
        
        # 역할 변환 (RegisterUserRole -> UserRole)
        if user_data.role == RegisterUserRole.FARMER:
            db_role = UserRole.FARMER
        else:
            db_role = UserRole.USER
        
        # 사용자 생성
        new_user = UserCRUD.create(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            full_name=user_data.full_name,
            role=db_role
        )
        
        # 데이터베이스 커밋
        try:
            db.commit()
            db.refresh(new_user)
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="회원가입 처리 중 데이터베이스 오류가 발생했습니다"
            )
        
        # 성공 응답
        return RegisterResponse(
            message="회원가입이 완료되었습니다",
            user_id=new_user.id
        )
        
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="사용자명 또는 이메일이 이미 사용 중입니다"
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원가입 처리 중 오류가 발생했습니다"
        )

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """로그인"""
    try:
        user = authenticate_user(db, user_credentials.username, user_credentials.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자명 또는 비밀번호가 올바르지 않습니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="비활성화된 계정입니다"
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, 
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            username=user.username,
            role=user.role.value  # 역할 정보 추가
        )
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 처리 중 오류가 발생했습니다"
        )

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """현재 로그인한 사용자 정보 조회"""
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat()
    }

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """로그아웃"""
    return {"message": "로그아웃되었습니다"}

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """토큰 갱신"""
    try:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(current_user.id)}, 
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=current_user.id,
            username=current_user.username,
            role=current_user.role.value  # 역할 정보 추가
        )
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="토큰 갱신 중 오류가 발생했습니다"
        )