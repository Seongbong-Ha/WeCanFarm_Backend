from fastapi import APIRouter, UploadFile, File, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import base64
from PIL import Image
from io import BytesIO
import os
import time

from ..services.pipeline import process_image_pipeline, process_single_crop_analysis
from ..database.database import get_db
from ..database.models import (
    AnalysisRequest as DBAnalysisRequest, 
    AnalysisResult as DBAnalysisResult,
    AnalysisType, 
    RequestStatus,
    AnalysisRequestCRUD,
    AnalysisResultCRUD
)

router = APIRouter()

# 임시 사용자 ID (analyze.py와 동일)
TEMP_USER_ID = 1

# ✅ 절대 경로로 templates 디렉토리 지정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.abspath(os.path.join(BASE_DIR, "../templates"))
templates = Jinja2Templates(directory=TEMPLATE_DIR)

@router.get("/", response_class=HTMLResponse)
async def upload_page(request: Request):
    """이미지 업로드 페이지"""
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/analyze_web", response_class=HTMLResponse)
async def analyze_web(request: Request, file: UploadFile = File(...), 
                     analysis_type: str = Form("pipeline"), db: Session = Depends(get_db)):
    """
    웹 UI 이미지 분석 - DB 연동 버전
    Args:
        file: 업로드된 이미지 파일
        analysis_type: "pipeline" (전체 파이프라인) 또는 "single" (단일 분석)
    """
    start_time = time.time()
    
    try:
        print("🌐 [WEB] 웹 분석 요청 시작")
        
        # 1. 파일을 PIL Image로 변환
        contents = await file.read()
        image = Image.open(BytesIO(contents))
        print(f"✅ [WEB] 이미지 로드 완료 - 크기: {image.size}")

        # 2. DB에 분석 요청 저장
        try:
            temp_image_url = f"web_{analysis_type}_{int(time.time())}.jpg"
            
            db_analysis_type = AnalysisType.PIPELINE if analysis_type == "pipeline" else AnalysisType.SINGLE
            
            db_request = AnalysisRequestCRUD.create(
                db=db,
                user_id=TEMP_USER_ID,
                image_url=temp_image_url,
                analysis_type=db_analysis_type
            )
            print(f"✅ [WEB] DB 요청 저장 완료 - ID: {db_request.id}")
            
        except Exception as e:
            print(f"❌ [WEB] DB 요청 저장 실패: {e}")
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error_message": f"요청 저장 실패: {str(e)}"
            })

        # 3. 상태를 PROCESSING으로 변경
        AnalysisRequestCRUD.update_status(db, db_request.id, RequestStatus.PROCESSING)

        # 4. 분석 타입에 따라 처리
        if analysis_type == "pipeline":
            # 전체 파이프라인 (YOLO + ResNet)
            print("🔍 [WEB] 전체 파이프라인 실행")
            result = process_image_pipeline(image)
            
            if result["processing_status"] != "성공":
                AnalysisRequestCRUD.update_status(db, db_request.id, RequestStatus.FAILED)
                return templates.TemplateResponse("error.html", {
                    "request": request,
                    "error_message": result["processing_status"]
                })
            
            # 결과 이미지는 이미 base64로 인코딩됨
            encoded_image = result["image_base64"]
            
            # DB에 결과 저장
            try:
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                db_result = AnalysisResultCRUD.create(
                    db=db,
                    request_id=db_request.id,
                    total_detections=result["total_detections"],
                    result_image_url=f"web_pipeline_result_{db_request.id}.jpg",
                    detection_data=result["detections"],
                    processing_status=result["processing_status"]
                )
                
                AnalysisRequestCRUD.update_status(
                    db, db_request.id, RequestStatus.COMPLETED, processing_time_ms
                )
                
                print(f"✅ [WEB] 파이프라인 결과 저장 완료 - {result['total_detections']}개 감지")
                
            except Exception as e:
                print(f"❌ [WEB] 결과 저장 실패: {e}")
                AnalysisRequestCRUD.update_status(db, db_request.id, RequestStatus.FAILED)
            
            return templates.TemplateResponse("pipeline_result.html", {
                "request": request,
                "image_base64": encoded_image,
                "detections": result["detections"],
                "total_detections": result["total_detections"],
                "analysis_type": "전체 파이프라인"
            })
            
        else:  # single
            # 단일 작물 분석 (기존 방식)
            print("🔍 [WEB] 단일 작물 분석 실행")
            result = process_single_crop_analysis(image, 'pepper')
            
            if result["disease_status"].startswith(("분석 실패", "이미지 유효성")):
                AnalysisRequestCRUD.update_status(db, db_request.id, RequestStatus.FAILED)
                return templates.TemplateResponse("error.html", {
                    "request": request,
                    "error_message": result["disease_status"]
                })
            
            # DB에 결과 저장
            try:
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                single_detection_data = [{
                    "crop_type": result["crop_type"],
                    "disease_status": result["disease_status"],
                    "confidence": result.get("confidence", 0.0),
                    "analysis_type": "single"
                }]
                
                db_result = AnalysisResultCRUD.create(
                    db=db,
                    request_id=db_request.id,
                    total_detections=1,
                    result_image_url=f"web_single_result_{db_request.id}.jpg",
                    detection_data=single_detection_data,
                    processing_status="성공"
                )
                
                AnalysisRequestCRUD.update_status(
                    db, db_request.id, RequestStatus.COMPLETED, processing_time_ms
                )
                
                print(f"✅ [WEB] 단일 분석 결과 저장 완료 - {result['disease_status']}")
                
            except Exception as e:
                print(f"❌ [WEB] 결과 저장 실패: {e}")
                AnalysisRequestCRUD.update_status(db, db_request.id, RequestStatus.FAILED)
            
            # 원본 이미지를 base64로 인코딩
            buffered = BytesIO()
            image.save(buffered, format="JPEG")
            encoded_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            return templates.TemplateResponse("single_result.html", {
                "request": request,
                "image_base64": encoded_image,
                "result": result,
                "analysis_type": "단일 분석"
            })
            
    except Exception as e:
        print(f"❌ [WEB] 처리 중 오류: {e}")
        
        # DB 상태 업데이트
        if 'db_request' in locals():
            try:
                AnalysisRequestCRUD.update_status(db, db_request.id, RequestStatus.FAILED)
            except:
                pass
        
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": f"처리 중 오류가 발생했습니다: {str(e)}"
        })

@router.get("/pipeline_demo", response_class=HTMLResponse)
async def pipeline_demo_page(request: Request):
    """파이프라인 데모 페이지"""
    return templates.TemplateResponse("pipeline_demo.html", {"request": request})