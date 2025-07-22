from fastapi import APIRouter, HTTPException
from ..schemas.request_response import AnalyzeRequest, AnalyzeResponse
from ..utils.image_handler import decode_base64_to_image
from ..services.inference import run_resnet_inference

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(req: AnalyzeRequest):
    try:
        # 1. base64 → 이미지 객체 변환
        image = decode_base64_to_image(req.image_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"이미지 디코딩 실패: {str(e)}")

    # 2. 모델 추론 수행
    result = run_resnet_inference(image)

    # 3. 모델 로딩 실패 시 500 에러 반환
    if result["disease_status"].startswith("모델 로딩 실패"):
        raise HTTPException(status_code=500, detail=result["disease_status"])

    return AnalyzeResponse(**result)
