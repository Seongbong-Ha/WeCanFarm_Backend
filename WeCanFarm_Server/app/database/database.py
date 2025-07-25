# WeCanFarm_Server/app/database/database.py
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

# 환경변수 로드 (.env 파일 경로 명시)
current_file = os.path.abspath(__file__)  # database.py 파일 경로
database_dir = os.path.dirname(current_file)  # database 디렉토리
app_dir = os.path.dirname(database_dir)  # app 디렉토리  
server_dir = os.path.dirname(app_dir)  # WeCanFarm_Server 디렉토리
env_path = os.path.join(server_dir, '.env')  # WeCanFarm_Server/.env

load_dotenv(env_path)

print(f"🔍 .env 파일 경로: {env_path}")
print(f"🔍 .env 파일 존재: {os.path.exists(env_path)}")

# 데이터베이스 URL 설정 (.env에서 가져오기)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL이 .env 파일에 설정되지 않았습니다!")

# 보안상 패스워드 부분은 숨겨서 출력
url_parts = DATABASE_URL.split('@')
if len(url_parts) == 2:
    masked_url = url_parts[0].split(':')[:-1] + ['***'] + ['@'] + [url_parts[1]]
    print(f"🔗 데이터베이스 연결: {''.join(masked_url)}")
else:
    print("🔗 데이터베이스 연결: [URL 확인됨]")

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # 연결 풀 크기
    max_overflow=20,  # 추가 연결 허용
    pool_pre_ping=True,  # 연결 상태 확인
    echo=False  # SQL 로그 출력 (개발시 True로 변경)
)

# 세션 팩토리
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# Base 클래스 (모든 모델의 부모 클래스)
Base = declarative_base()

# 의존성 주입용 DB 세션
def get_db():
    """FastAPI 의존성 주입용 DB 세션"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

# 데이터베이스 연결 테스트
def test_connection():
    """데이터베이스 연결 테스트"""
    try:
        with engine.connect() as conn:
            # SQLAlchemy 2.0 스타일
            from sqlalchemy import text
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL 연결 성공!")
            print(f"📋 버전: {version}")
            return True
    except Exception as e:
        print(f"❌ PostgreSQL 연결 실패: {e}")
        return False

# 데이터베이스 초기화
def create_tables():
    """데이터베이스 테이블 생성"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ 데이터베이스 테이블 생성 완료")
        return True
    except Exception as e:
        print(f"❌ 테이블 생성 실패: {e}")
        return False

# 테이블 삭제 (개발용)
def drop_tables():
    """모든 테이블 삭제 (주의: 데이터 손실)"""
    try:
        Base.metadata.drop_all(bind=engine)
        print("⚠️ 모든 테이블 삭제 완료")
        return True
    except Exception as e:
        print(f"❌ 테이블 삭제 실패: {e}")
        return False