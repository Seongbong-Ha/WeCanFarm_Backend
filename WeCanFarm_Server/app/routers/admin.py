from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import Dict, Any
import os

from ..database.database import get_db
from ..database.models import User, AnalysisRequest, AnalysisResult, Crop, Disease, UserRole

router = APIRouter(prefix="/admin", tags=["admin"])

# 템플릿 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.abspath(os.path.join(BASE_DIR, "../templates"))
templates = Jinja2Templates(directory=TEMPLATE_DIR)

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard_page(request: Request, db: Session = Depends(get_db)):
    """관리자 대시보드 메인 페이지"""
    try:
        # 통계 데이터 수집
        stats = get_dashboard_stats(db)
        
        return templates.TemplateResponse("admin_dashboard.html", {
            "request": request,
            "stats": stats
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": f"대시보드 로딩 실패: {str(e)}"
        })

@router.get("/dashboard/api")
async def get_dashboard_stats_api(db: Session = Depends(get_db)):
    """대시보드 통계 데이터 API (AJAX용)"""
    try:
        stats = get_dashboard_stats(db)
        return {"success": True, "data": stats}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_dashboard_stats(db: Session) -> Dict[str, Any]:
    """대시보드 통계 데이터 수집"""
    
    # 현재 시간 기준
    now = datetime.now()
    last_30_days = now - timedelta(days=30)
    today = now.date()
    
    # 1. 사용자 통계
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    new_users_30d = db.query(User).filter(User.created_at >= last_30_days).count()
    
    # 사용자 유형별 통계
    user_types = db.query(
        User.role, 
        func.count(User.id).label('count')
    ).group_by(User.role).all()
    
    user_type_stats = {}
    for role, count in user_types:
        user_type_stats[role.value] = count
    
    # 2. 분석 통계
    total_analyses = db.query(AnalysisRequest).count()
    analyses_30d = db.query(AnalysisRequest).filter(
        AnalysisRequest.created_at >= last_30_days
    ).count()
    
    # 오늘 분석 수
    today_analyses = db.query(AnalysisRequest).filter(
        func.date(AnalysisRequest.created_at) == today
    ).count()
    
    # 3. 작물별 분석량 (JSON에서 추출 필요)
    # 일단 간단하게 요청 수로 계산
    crop_analysis_stats = {}
    
    # 모든 작물 목록 가져오기
    crops = db.query(Crop).all()
    for crop in crops:
        # 해당 작물 관련 분석 요청 수 (임시로 전체 분석 수로 계산)
        # 실제로는 detection_data JSON에서 추출해야 함
        count = db.query(AnalysisRequest).count() if crop.name == "pepper" else 0
        crop_analysis_stats[crop.name] = count
    
    # 4. 질병 감지율
    completed_results = db.query(AnalysisResult).filter(
        AnalysisResult.processing_status == "성공"
    ).all()
    
    total_detections = 0
    normal_detections = 0
    disease_detections = 0
    
    for result in completed_results:
        if result.detection_data and isinstance(result.detection_data, list):
            for detection in result.detection_data:
                total_detections += 1
                if detection.get('disease_status') == '정상':
                    normal_detections += 1
                else:
                    disease_detections += 1
    
    # 질병별 통계
    disease_stats = {}
    diseases = db.query(Disease).all()
    for disease in diseases:
        # 실제로는 detection_data에서 추출해야 함
        if disease.name == "normal_0":
            disease_stats["정상"] = normal_detections
        elif disease.name == "BacterialSpot_4":
            disease_stats["고추점무늬병"] = disease_detections // 2 if disease_detections > 0 else 0
        elif disease.name == "PMMoV_3":
            disease_stats["고추마일드모틀바이러스"] = disease_detections // 2 if disease_detections > 0 else 0
    
    # 5. 성공률 계산
    total_requests = db.query(AnalysisRequest).count()
    completed_requests = db.query(AnalysisRequest).filter(
        AnalysisRequest.status == "COMPLETED"
    ).count()
    
    success_rate = (completed_requests / total_requests * 100) if total_requests > 0 else 0
    
    return {
        "user_stats": {
            "total_users": total_users,
            "active_users": active_users,
            "new_users_30d": new_users_30d,
            "user_types": user_type_stats
        },
        "analysis_stats": {
            "total_analyses": total_analyses,
            "analyses_30d": analyses_30d,
            "today_analyses": today_analyses,
            "success_rate": round(success_rate, 1)
        },
        "crop_stats": crop_analysis_stats,
        "disease_stats": disease_stats,
        "detection_summary": {
            "total_detections": total_detections,
            "normal_rate": round((normal_detections / total_detections * 100) if total_detections > 0 else 0, 1),
            "disease_rate": round((disease_detections / total_detections * 100) if total_detections > 0 else 0, 1)
        },
        "last_updated": now.strftime("%Y-%m-%d %H:%M:%S")
    }