from fastapi import APIRouter, HTTPException
from ..schemas.request_response import (
    AnalyzeRequest, 
    AnalyzeResponse, 
    SingleAnalyzeResponse,
    DetectionResult
)
from ..utils.image_handler import decode_base64_to_image
from ..services.pipeline import process_image_pipeline, process_single_crop_analysis

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(req: AnalyzeRequest):
    """
    이미지 분석 API (전체 파이프라인)
    - YOLO 객체 감지 → ResNet 질병 분류 → 결과 시각화
    """
    try:
        # 1. base64 → 이미지 객체 변환
        image = decode_base64_to_image(req.image_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"이미지 디코딩 실패: {str(e)}")

    # 2. 전체 파이프라인 실행
    result = process_image_pipeline(image)

    # 3. 처리 실패 시 500 에러 반환
    if result["processing_status"] != "성공":
        raise HTTPException(status_code=500, detail=result["processing_status"])

    # 4. 응답 데이터 구성
    return AnalyzeResponse(
        image_base64=result["image_base64"],
        detections=result["detections"],
        total_detections=result["total_detections"]
    )

@router.post("/analyze_single", response_model=SingleAnalyzeResponse)
async def analyze_single_crop(req: AnalyzeRequest, crop_type: str = "pepper"):
    """
    단일 작물 분석 API (기존 방식)
    - YOLO 없이 ResNet으로 직접 분석
    """
    try:
        # 1. base64 → 이미지 객체 변환
        image = decode_base64_to_image(req.image_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"이미지 디코딩 실패: {str(e)}")

    # 2. 단일 작물 분석
    result = process_single_crop_analysis(image, crop_type)

    # 3. 분석 실패 시 500 에러 반환
    if result["disease_status"].startswith(("분석 실패", "이미지 유효성")):
        raise HTTPException(status_code=500, detail=result["disease_status"])

    return {
        "crop_type": result["crop_type"],
        "disease_status": result["disease_status"],
        "confidence": result.get("confidence", 0.0)
    }