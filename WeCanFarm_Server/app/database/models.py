from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum

# Enum 클래스 정의
class UserRole(enum.Enum):
    USER = "USER"
    FARMER = "FARMER"
    ADMIN = "ADMIN"

class AnalysisType(enum.Enum):
    PIPELINE = "PIPELINE"
    SINGLE = "SINGLE"

class RequestStatus(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

# 사용자 모델
class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)  # 해시된 비밀번호
    full_name = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    
    # 관계 설정
    analysis_requests = relationship("AnalysisRequest", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

# 작물 모델
class Crop(Base):
    __tablename__ = "crops"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)  # pepper, tomato, cucumber
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    diseases = relationship("Disease", back_populates="crop", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Crop(id={self.id}, name='{self.name}')>"

# 질병 모델
class Disease(Base):
    __tablename__ = "diseases"
    
    id = Column(Integer, primary_key=True, index=True)
    crop_id = Column(Integer, ForeignKey("crops.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)  # BacterialSpot_4, PMMoV_3, normal_0
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    crop = relationship("Crop", back_populates="diseases")
    
    def __repr__(self):
        return f"<Disease(id={self.id}, name='{self.name}', crop_id={self.crop_id})>"

# 분석 요청 모델
class AnalysisRequest(Base):
    __tablename__ = "analysis_requests"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String(500), nullable=False)
    analysis_type = Column(Enum(AnalysisType), default=AnalysisType.PIPELINE)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    processing_time = Column(Integer)  # 처리 시간 (밀리초)
    
    # 관계 설정
    user = relationship("User", back_populates="analysis_requests")
    result = relationship("AnalysisResult", back_populates="request", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AnalysisRequest(id={self.id}, user_id={self.user_id}, status='{self.status.value}')>"

# 분석 결과 모델
class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(BigInteger, primary_key=True, index=True)
    request_id = Column(BigInteger, ForeignKey("analysis_requests.id", ondelete="CASCADE"), nullable=False)
    total_detections = Column(Integer, default=0)
    result_image_url = Column(String(500))
    detection_data = Column(JSON)  # PostgreSQL JSON 필드 - 모든 감지 결과 저장
    processing_status = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    request = relationship("AnalysisRequest", back_populates="result")
    
    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, request_id={self.request_id}, total_detections={self.total_detections})>"

# 모델 헬퍼 함수들
class UserCRUD:
    """사용자 관련 CRUD 함수들"""
    
    @staticmethod
    def get_by_email(db, email: str):
        """이메일로 사용자 조회"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_by_username(db, username: str):
        """사용자명으로 사용자 조회"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_by_id(db, user_id: int):
        """ID로 사용자 조회"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def create(db, username: str, email: str, password_hash: str, full_name: str = None, role: UserRole = UserRole.USER):
        """새 사용자 생성"""
        db_user = User(
            username=username,
            email=email,
            password=password_hash,
            full_name=full_name,
            role=role
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def update_last_login(db, user_id: int):
        """마지막 로그인 시간 업데이트"""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.last_login = func.now()
            db.commit()
        return user

class CropCRUD:
    """작물 관련 CRUD 함수들"""
    
    @staticmethod
    def get_by_name(db, crop_name: str):
        """작물명으로 작물 조회"""
        return db.query(Crop).filter(Crop.name == crop_name).first()
    
    @staticmethod
    def get_all(db):
        """모든 작물 조회"""
        return db.query(Crop).all()
    
    @staticmethod
    def create(db, name: str):
        """새 작물 생성"""
        db_crop = Crop(name=name)
        db.add(db_crop)
        db.commit()
        db.refresh(db_crop)
        return db_crop

class DiseaseCRUD:
    """질병 관련 CRUD 함수들"""
    
    @staticmethod
    def get_by_crop_id(db, crop_id: int):
        """작물별 질병 목록 조회"""
        return db.query(Disease).filter(Disease.crop_id == crop_id).all()
    
    @staticmethod
    def get_by_name(db, disease_name: str):
        """질병명으로 질병 조회"""
        return db.query(Disease).filter(Disease.name == disease_name).first()
    
    @staticmethod
    def create(db, crop_id: int, name: str):
        """새 질병 생성"""
        db_disease = Disease(crop_id=crop_id, name=name)
        db.add(db_disease)
        db.commit()
        db.refresh(db_disease)
        return db_disease

class AnalysisRequestCRUD:
    """분석 요청 관련 CRUD 함수들"""
    
    @staticmethod
    def create(db, user_id: int, image_url: str, analysis_type: AnalysisType = AnalysisType.PIPELINE):
        """분석 요청 생성"""
        db_request = AnalysisRequest(
            user_id=user_id,
            image_url=image_url,
            analysis_type=analysis_type
        )
        db.add(db_request)
        db.commit()
        db.refresh(db_request)
        return db_request
    
    @staticmethod
    def update_status(db, request_id: int, status: RequestStatus, processing_time: int = None):
        """요청 상태 업데이트"""
        request = db.query(AnalysisRequest).filter(AnalysisRequest.id == request_id).first()
        if request:
            request.status = status
            if processing_time is not None:
                request.processing_time = processing_time
            db.commit()
        return request
    
    @staticmethod
    def get_user_history(db, user_id: int, limit: int = 10):
        """사용자 분석 이력 조회"""
        return db.query(AnalysisRequest).filter(
            AnalysisRequest.user_id == user_id
        ).order_by(AnalysisRequest.created_at.desc()).limit(limit).all()

class AnalysisResultCRUD:
    """분석 결과 관련 CRUD 함수들"""
    
    @staticmethod
    def create(db, request_id: int, total_detections: int, result_image_url: str, 
              detection_data: dict, processing_status: str):
        """분석 결과 생성"""
        db_result = AnalysisResult(
            request_id=request_id,
            total_detections=total_detections,
            result_image_url=result_image_url,
            detection_data=detection_data,
            processing_status=processing_status
        )
        db.add(db_result)
        db.commit()
        db.refresh(db_result)
        return db_result
    
    @staticmethod
    def get_by_request_id(db, request_id: int):
        """요청 ID로 결과 조회"""
        return db.query(AnalysisResult).filter(AnalysisResult.request_id == request_id).first()