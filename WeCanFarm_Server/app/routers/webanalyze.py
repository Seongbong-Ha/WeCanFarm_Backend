# routers/webanalyze.py
from fastapi import APIRouter, UploadFile, File, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import base64
from PIL import Image
from io import BytesIO
import os
from ..services.pipeline import process_image_pipeline, process_single_crop_analysis

router = APIRouter()

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
                     analysis_type: str = Form("pipeline")):
    """
    웹 UI 이미지 분석
    Args:
        file: 업로드된 이미지 파일
        analysis_type: "pipeline" (전체 파이프라인) 또는 "single" (단일 분석)
    """
    try:
        # 1. 파일을 PIL Image로 변환
        contents = await file.read()
        image = Image.open(BytesIO(contents))

        # 2. 분석 타입에 따라 처리
        if analysis_type == "pipeline":
            # 전체 파이프라인 (YOLO + ResNet)
            result = process_image_pipeline(image)
            
            if result["processing_status"] != "성공":
                return templates.TemplateResponse("error.html", {
                    "request": request,
                    "error_message": result["processing_status"]
                })
            
            # 결과 이미지는 이미 base64로 인코딩됨
            encoded_image = result["image_base64"]
            
            return templates.TemplateResponse("pipeline_result.html", {
                "request": request,
                "image_base64": encoded_image,
                "detections": result["detections"],
                "total_detections": result["total_detections"],
                "analysis_type": "전체 파이프라인"
            })
            
        else:  # single
            # 단일 작물 분석 (기존 방식)
            result = process_single_crop_analysis(image, 'pepper')
            
            if result["disease_status"].startswith(("분석 실패", "이미지 유효성")):
                return templates.TemplateResponse("error.html", {
                    "request": request,
                    "error_message": result["disease_status"]
                })
            
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
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": f"처리 중 오류가 발생했습니다: {str(e)}"
        })

@router.get("/pipeline_demo", response_class=HTMLResponse)
async def pipeline_demo_page(request: Request):
    """파이프라인 데모 페이지"""
    return templates.TemplateResponse("pipeline_demo.html", {"request": request})