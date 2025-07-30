from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import logging

# 기본 인자 설정
default_args = {
    'owner': 'wecanfarm-analyst',
    'depends_on_past': False,
    'start_date': datetime(2025, 7, 30),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG 정의
dag = DAG(
    'wecanfarm_daily_stats',
    default_args=default_args,
    description='WeCanFarm 간단한 일일 통계 수집',
    schedule='0 9 * * *',  # 매일 오전 9시 실행
    catchup=False,
    tags=['wecanfarm', 'analytics', 'daily', 'portfolio']
)

def collect_daily_stats(**context):
    """어제 하루 간단한 통계 수집"""
    
    # 어제 날짜 계산
    execution_date = context['ds']  # YYYY-MM-DD 형식
    logging.info(f"📅 수집 대상 날짜: {execution_date}")
    
    try:
        # PostgresHook을 사용해서 연결
        postgres_hook = PostgresHook(postgres_conn_id='wecanfarm_db')
        
        logging.info("🔍 일일 통계 수집 시작...")
        
        # 1. 어제 신규 가입자 수
        new_users_query = """
        SELECT COUNT(*) as new_users
        FROM users 
        WHERE DATE(created_at) = %s
        """
        new_users = postgres_hook.get_first(new_users_query, parameters=[execution_date])
        new_users_count = new_users[0] if new_users else 0
        
        # 2. 어제 분석 요청 수
        analysis_requests_query = """
        SELECT COUNT(*) as total_requests
        FROM analysis_requests 
        WHERE DATE(created_at) = %s
        """
        analysis_requests = postgres_hook.get_first(analysis_requests_query, parameters=[execution_date])
        requests_count = analysis_requests[0] if analysis_requests else 0
        
        # 3. 어제 성공한 분석 수
        successful_analysis_query = """
        SELECT COUNT(*) as successful_requests
        FROM analysis_requests 
        WHERE DATE(created_at) = %s 
          AND status = 'COMPLETED'
        """
        successful_analysis = postgres_hook.get_first(successful_analysis_query, parameters=[execution_date])
        successful_count = successful_analysis[0] if successful_analysis else 0
        
        # 4. 성공률 계산
        success_rate = (successful_count / requests_count * 100) if requests_count > 0 else 0
        
        # 5. 총 누적 통계
        total_users_query = "SELECT COUNT(*) FROM users"
        total_users = postgres_hook.get_first(total_users_query)
        total_users_count = total_users[0] if total_users else 0
        
        # 결과 정리
        daily_stats = {
            'date': execution_date,
            'new_users': new_users_count,
            'total_requests': requests_count,
            'successful_requests': successful_count,
            'success_rate': round(success_rate, 2),
            'total_users_cumulative': total_users_count
        }
        
        # 결과 로깅 (이쁘게 출력)
        logging.info("=" * 50)
        logging.info(f"📊 WeCanFarm 일일 리포트 - {execution_date}")
        logging.info("=" * 50)
        logging.info(f"👥 신규 가입자: {new_users_count}명")
        logging.info(f"📈 분석 요청: {requests_count}건")
        logging.info(f"✅ 성공한 분석: {successful_count}건")
        logging.info(f"📊 성공률: {success_rate:.1f}%")
        logging.info(f"👥 총 사용자: {total_users_count}명 (누적)")
        logging.info("=" * 50)
        
        # 실제 운영에서는 이 데이터를 별도 테이블에 저장하거나 
        # 외부 시스템으로 전송할 수 있습니다
        
        logging.info("✅ 일일 통계 수집 완료!")
        return daily_stats
        
    except Exception as e:
        logging.error(f"❌ 일일 통계 수집 실패: {str(e)}")
        raise e

def send_summary_report(**context):
    """간단한 요약 리포트 생성"""
    
    # 이전 task의 결과 가져오기
    ti = context['ti']
    daily_stats = ti.xcom_pull(task_ids='collect_daily_statistics')
    
    if not daily_stats:
        logging.error("❌ 통계 데이터를 가져올 수 없습니다")
        return
    
    logging.info("📋 요약 리포트 생성 중...")
    
    # 간단한 알림 메시지 형태로 요약
    summary = f"""
    🌱 WeCanFarm 일일 요약 ({daily_stats['date']})
    
    📊 주요 지표:
    • 신규 가입자: {daily_stats['new_users']}명
    • 분석 요청: {daily_stats['total_requests']}건
    • 성공률: {daily_stats['success_rate']}%
    
    📈 누적 현황:
    • 총 사용자: {daily_stats['total_users_cumulative']}명
    
    ✨ 오늘도 농작물 건강 관리에 도움이 되었습니다!
    """
    
    logging.info(summary)
    
    # 실제 운영에서는 Slack, 이메일, 대시보드로 전송 가능
    logging.info("✅ 요약 리포트 생성 완료!")
    
    return summary

# Task 정의
collect_stats_task = PythonOperator(
    task_id='collect_daily_statistics',
    python_callable=collect_daily_stats,
    dag=dag,
)

summary_report_task = PythonOperator(
    task_id='generate_summary_report',
    python_callable=send_summary_report,
    dag=dag,
)

# Task 의존성 설정
collect_stats_task >> summary_report_task