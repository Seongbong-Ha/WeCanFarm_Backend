import sys
import os

# 현재 파일의 위치를 기준으로 프로젝트 루트 찾기
current_dir = os.path.dirname(os.path.abspath(__file__))  # database 폴더
app_dir = os.path.dirname(current_dir)  # app 폴더
project_root = os.path.dirname(app_dir)  # WeCanFarm_Server 폴더
sys.path.append(project_root)

# 상대 경로로 import
try:
    from app.database.database import drop_tables, create_tables
    from app.database.init_db import insert_initial_data
except ImportError:
    # 함수가 없다면 기본 방식으로
    from app.database.database import engine, Base
    from app.database.models import *
    
    def drop_tables():
        Base.metadata.drop_all(bind=engine)
        print("✅ 테이블 삭제 완료")
    
    def create_tables():
        Base.metadata.create_all(bind=engine)
        print("✅ 테이블 생성 완료")
    
    def insert_initial_data():
        print("ℹ️ 초기 데이터 삽입 스킵 (함수 없음)")

def simple_reset():
    """간단한 데이터베이스 초기화"""
    print("🔄 데이터베이스 초기화 시작...")
    
    try:
        # 1. 테이블 삭제
        print("📋 기존 테이블 삭제 중...")
        drop_tables()
        
        # 2. 테이블 재생성
        print("🔨 테이블 생성 중...")
        create_tables()
        
        # 3. 기본 데이터 삽입
        print("💾 초기 데이터 삽입 중...")
        insert_initial_data()
        
        print("✅ 초기화 완료!")
        
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")

if __name__ == "__main__":
    simple_reset()