from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import logging

# 기본 인자 설정
default_args = {
    'owner': 'wecanfarm-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 7, 29),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG 정의
dag = DAG(
    'wecanfarm_connection_test',
    default_args=default_args,
    description='WeCanFarm 데이터베이스 연결 테스트',
    schedule=None,  # 수동 실행만 (Airflow 3.0+)
    catchup=False,
    tags=['wecanfarm', 'test', 'connection']
)

def test_wecanfarm_connection(**context):
    """WeCanFarm 데이터베이스 연결 테스트"""
    try:
        # PostgresHook을 사용해서 연결
        postgres_hook = PostgresHook(postgres_conn_id='wecanfarm_db')
        
        logging.info("🔍 WeCanFarm 데이터베이스 연결 시도...")
        
        # 간단한 연결 테스트
        connection = postgres_hook.get_conn()
        cursor = connection.cursor()
        
        # 데이터베이스 버전 확인
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logging.info(f"✅ 데이터베이스 연결 성공!")
        logging.info(f"📊 PostgreSQL 버전: {version}")
        
        # 기본 테이블 존재 확인
        tables_to_check = ['users', 'analysis_requests', 'analysis_results']
        
        for table_name in tables_to_check:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                );
            """)
            exists = cursor.fetchone()[0]
            
            if exists:
                # 테이블 레코드 수 확인
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                logging.info(f"✅ 테이블 '{table_name}': {count}개 레코드")
            else:
                logging.warning(f"⚠️ 테이블 '{table_name}'이 존재하지 않습니다")
        
        cursor.close()
        connection.close()
        
        logging.info("🎉 WeCanFarm 데이터베이스 연결 테스트 완료!")
        return "연결 테스트 성공"
        
    except Exception as e:
        logging.error(f"❌ 데이터베이스 연결 실패: {str(e)}")
        raise e

def test_basic_query(**context):
    """기본 쿼리 테스트"""
    try:
        postgres_hook = PostgresHook(postgres_conn_id='wecanfarm_db')
        
        logging.info("🔍 기본 쿼리 테스트 시작...")
        
        # 사용자 수 조회
        user_count = postgres_hook.get_first("SELECT COUNT(*) FROM users;")
        logging.info(f"👥 총 사용자 수: {user_count[0]}명")
        
        # 분석 요청 수 조회 (있다면)
        try:
            analysis_count = postgres_hook.get_first("SELECT COUNT(*) FROM analysis_requests;")
            logging.info(f"📊 총 분석 요청 수: {analysis_count[0]}건")
        except Exception as e:
            logging.info(f"📊 분석 요청 테이블 조회 실패: {e}")
        
        # 최근 생성된 사용자 조회 (최대 5명)
        recent_users = postgres_hook.get_records("""
            SELECT username, created_at 
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 5;
        """)
        
        logging.info("👤 최근 가입한 사용자들:")
        for user in recent_users:
            logging.info(f"   - {user[0]} ({user[1]})")
        
        logging.info("✅ 기본 쿼리 테스트 완료!")
        return "쿼리 테스트 성공"
        
    except Exception as e:
        logging.error(f"❌ 쿼리 테스트 실패: {str(e)}")
        raise e

# Task 정의
test_connection_task = PythonOperator(
    task_id='test_database_connection',
    python_callable=test_wecanfarm_connection,
    dag=dag,
)

test_query_task = PythonOperator(
    task_id='test_basic_queries',
    python_callable=test_basic_query,
    dag=dag,
)

# Task 의존성 설정
test_connection_task >> test_query_task