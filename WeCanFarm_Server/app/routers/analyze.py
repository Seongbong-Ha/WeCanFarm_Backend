from fastapi import APIRouter, HTTPException, Request
import json
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
        # 🔍 디버깅 로그 1: 요청 데이터 확인
        print("=" * 50)
        print("🔍 [DEBUG] 새로운 analyze 요청 받음")
        print(f"🔍 [DEBUG] image_base64 타입: {type(req.image_base64)}")
        
        if req.image_base64:
            print(f"🔍 [DEBUG] image_base64 길이: {len(req.image_base64)}")
            print(f"🔍 [DEBUG] image_base64 첫 30글자: {req.image_base64[:30]}")
            print(f"🔍 [DEBUG] image_base64 마지막 10글자: {req.image_base64[-10:]}")
        else:
            print("❌ [DEBUG] image_base64가 None 또는 빈 문자열")
            raise HTTPException(status_code=400, detail="image_base64 필드가 없거나 비어있습니다")
        
        # 🔍 디버깅 로그 2: base64 → 이미지 변환 시도
        print("🔍 [DEBUG] base64 → 이미지 변환 시작")
        image = decode_base64_to_image(req.image_base64)
        print(f"🔍 [DEBUG] 이미지 변환 성공 - 크기: {image.size}, 모드: {image.mode}")
        
    except ValueError as ve:
        print(f"❌ [DEBUG] ValueError: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Base64 디코딩 오류: {str(ve)}")
    except Exception as e:
        print(f"❌ [DEBUG] 이미지 디코딩 실패: {str(e)}")
        print(f"❌ [DEBUG] 에러 타입: {type(e)}")
        raise HTTPException(status_code=400, detail=f"이미지 디코딩 실패: {str(e)}")

    # 🔍 디버깅 로그 3: 파이프라인 실행
    print("🔍 [DEBUG] 파이프라인 실행 시작")
    try:
        result = process_image_pipeline(image)
        print(f"🔍 [DEBUG] 파이프라인 실행 결과: {result['processing_status']}")
        print(f"🔍 [DEBUG] 총 감지 개수: {result.get('total_detections', 0)}")
    except Exception as e:
        print(f"❌ [DEBUG] 파이프라인 실행 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"파이프라인 실행 실패: {str(e)}")

    # 🔍 디버깅 로그 4: 처리 결과 확인
    if result["processing_status"] != "성공":
        print(f"❌ [DEBUG] 파이프라인 처리 실패: {result['processing_status']}")
        raise HTTPException(status_code=500, detail=result["processing_status"])

    # 🔍 디버깅 로그 5: 응답 생성
    print("🔍 [DEBUG] 응답 생성 시작")
    try:
        response = AnalyzeResponse(
            image_base64=result["image_base64"],
            detections=result["detections"],
            total_detections=result["total_detections"]
        )
        print("✅ [DEBUG] 응답 생성 성공")
        print("=" * 50)
        return response
    except Exception as e:
        print(f"❌ [DEBUG] 응답 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"응답 생성 실패: {str(e)}")

@router.post("/analyze_single", response_model=SingleAnalyzeResponse)
async def analyze_single_crop(req: AnalyzeRequest, crop_type: str = "pepper"):
    """
    단일 작물 분석 API (기존 방식)
    - YOLO 없이 ResNet으로 직접 분석
    """
    try:
        # 🔍 디버깅 로그
        print("=" * 50)
        print("🔍 [DEBUG] 새로운 analyze_single 요청 받음")
        print(f"🔍 [DEBUG] crop_type: {crop_type}")
        
        if req.image_base64:
            print(f"🔍 [DEBUG] image_base64 길이: {len(req.image_base64)}")
        else:
            print("❌ [DEBUG] image_base64가 없음")
            raise HTTPException(status_code=400, detail="image_base64 필드가 필요합니다")
        
        # base64 → 이미지 객체 변환
        image = decode_base64_to_image(req.image_base64)
        print(f"✅ [DEBUG] 이미지 변환 성공: {image.size}")
        
    except Exception as e:
        print(f"❌ [DEBUG] 이미지 디코딩 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=f"이미지 디코딩 실패: {str(e)}")

    # 단일 작물 분석
    try:
        result = process_single_crop_analysis(image, crop_type)
        print(f"✅ [DEBUG] 단일 분석 완료: {result.get('disease_status', 'unknown')}")
    except Exception as e:
        print(f"❌ [DEBUG] 단일 분석 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")

    # 분석 실패 시 500 에러 반환
    if result["disease_status"].startswith(("분석 실패", "이미지 유효성")):
        print(f"❌ [DEBUG] 분석 결과 오류: {result['disease_status']}")
        raise HTTPException(status_code=500, detail=result["disease_status"])

    print("✅ [DEBUG] analyze_single 완료")
    print("=" * 50)
    return {
        "crop_type": result["crop_type"],
        "disease_status": result["disease_status"],
        "confidence": result.get("confidence", 0.0)
    }