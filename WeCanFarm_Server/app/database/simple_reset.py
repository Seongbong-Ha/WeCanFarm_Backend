import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from WeCanFarm_Server.app.database.database import drop_tables, create_tables
from WeCanFarm_Server.app.database.init_db import insert_initial_data

def simple_reset():
    """간단한 데이터베이스 초기화"""
    print("🔄 데이터베이스 초기화 시작...")
    
    # 1. 테이블 삭제
    drop_tables()
    
    # 2. 테이블 재생성
    create_tables()
    
    # 3. 기본 데이터 삽입
    insert_initial_data()
    
    print("✅ 초기화 완료!")

if __name__ == "__main__":
    simple_reset()