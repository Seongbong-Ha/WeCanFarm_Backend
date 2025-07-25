from sqlalchemy.orm import Session
from .database import engine, test_connection, create_tables, SessionLocal
from .models import User, Crop, Disease, UserRole, UserCRUD, CropCRUD, DiseaseCRUD

def init_database():
    """데이터베이스 초기화"""
    print("🚀 데이터베이스 초기화 시작...")
    
    # 1. 연결 테스트
    if not test_connection():
        print("❌ 데이터베이스 연결 실패. 초기화를 중단합니다.")
        return False
    
    # 2. 테이블 생성
    if not create_tables():
        print("❌ 테이블 생성 실패. 초기화를 중단합니다.")
        return False
    
    # 3. 기본 데이터 삽입
    insert_initial_data()
    
    print("✅ 데이터베이스 초기화 완료!")
    return True

def insert_initial_data():
    """기본 데이터 삽입"""
    db = SessionLocal()
    try:
        print("📊 기본 데이터 삽입 중...")
        
        # 1. 작물 데이터 삽입
        crops_data = [
            {"name": "pepper"},
            {"name": "tomato"},
            {"name": "cucumber"}
        ]
        
        for crop_data in crops_data:
            existing_crop = CropCRUD.get_by_name(db, crop_data["name"])
            if not existing_crop:
                CropCRUD.create(db, crop_data["name"])
                print(f"  ✅ 작물 추가: {crop_data['name']}")
            else:
                print(f"  ⏭ 작물 이미 존재: {crop_data['name']}")
        
        # 2. 질병 데이터 삽입 (고추 질병)
        pepper_crop = CropCRUD.get_by_name(db, "pepper")
        if pepper_crop:
            diseases_data = [
                {"crop_id": pepper_crop.id, "name": "normal_0"},
                {"crop_id": pepper_crop.id, "name": "BacterialSpot_4"},
                {"crop_id": pepper_crop.id, "name": "PMMoV_3"}
            ]
            
            for disease_data in diseases_data:
                existing_disease = DiseaseCRUD.get_by_name(db, disease_data["name"])
                if not existing_disease:
                    DiseaseCRUD.create(db, disease_data["crop_id"], disease_data["name"])
                    print(f"  ✅ 질병 추가: {disease_data['name']}")
                else:
                    print(f"  ⏭ 질병 이미 존재: {disease_data['name']}")
        
        # 3. 테스트 사용자 생성 (선택적)
        test_users = [
            {
                "username": "testuser",
                "email": "test@wecanfarm.com", 
                "password": "hashed_password_here",  # 실제로는 해시된 비밀번호
                "full_name": "테스트 사용자",
                "role": UserRole.USER
            },
            {
                "username": "testfarmer",
                "email": "farmer@wecanfarm.com",
                "password": "hashed_password_here",
                "full_name": "테스트 농부",
                "role": UserRole.FARMER
            }
        ]
        
        for user_data in test_users:
            existing_user = UserCRUD.get_by_email(db, user_data["email"])
            if not existing_user:
                UserCRUD.create(
                    db,
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=user_data["password"],
                    full_name=user_data["full_name"],
                    role=user_data["role"]
                )
                print(f"  ✅ 테스트 사용자 추가: {user_data['username']}")
            else:
                print(f"  ⏭ 사용자 이미 존재: {user_data['username']}")
        
        print("📊 기본 데이터 삽입 완료")
        
    except Exception as e:
        print(f"❌ 기본 데이터 삽입 실패: {e}")
        db.rollback()
    finally:
        db.close()

def check_database_status():
    """데이터베이스 상태 확인"""
    db = SessionLocal()
    try:
        print("🔍 데이터베이스 상태 확인...")
        
        # 사용자 수 확인
        user_count = db.query(User).count()
        print(f"👥 총 사용자 수: {user_count}")
        
        # 작물 수 확인
        crop_count = db.query(Crop).count()
        print(f"🌱 총 작물 수: {crop_count}")
        
        # 질병 수 확인
        disease_count = db.query(Disease).count()
        print(f"🦠 총 질병 수: {disease_count}")
        
        # 작물별 질병 확인
        crops = CropCRUD.get_all(db)
        for crop in crops:
            diseases = DiseaseCRUD.get_by_crop_id(db, crop.id)
            print(f"  {crop.name}: {len(diseases)}개 질병")
        
        return True
        
    except Exception as e:
        print(f"❌ 상태 확인 실패: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # 데이터베이스 초기화 실행
    success = init_database()
    
    if success:
        # 상태 확인
        check_database_status()
    else:
        print("❌ 데이터베이스 초기화 실패")