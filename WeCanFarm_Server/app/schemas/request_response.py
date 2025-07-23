from pydantic import BaseModel
from typing import List, Optional

class AnalyzeRequest(BaseModel):
    image_base64: str  # 안드로이드 앱에서 전송된 base64 인코딩 이미지

class DetectionResult(BaseModel):
    """개별 감지 결과"""
    bbox: List[int]           # [x1, y1, x2, y2] 형태의 바운딩 박스
    crop_type: str            # 작물 종류 (예: "pepper", "tomato")
    disease_status: str       # 질병 상태 (예: "정상", "고추점무늬병")
    disease_confidence: float # 질병 분류 신뢰도 (0.0 ~ 1.0)
    yolo_confidence: float    # YOLO 감지 신뢰도 (0.0 ~ 1.0)
    label: str                # 표시용 라벨 (예: "pepper: 고추점무늬병")

class AnalyzeResponse(BaseModel):
    """전체 파이프라인 분석 결과"""
    image_base64: str                    # 바운딩박스가 그려진 최종 이미지
    detections: List[DetectionResult]    # 감지된 객체들의 분석 결과
    total_detections: int                # 총 감지된 객체 수

class SingleAnalyzeResponse(BaseModel):
    """단일 작물 분석 결과 (기존 방식)"""
    crop_type: str           # 작물 종류
    disease_status: str      # 질병 상태
    confidence: float        # 신뢰도

# 웹 UI용 응답 (기존 호환성 유지)
class WebAnalyzeResult(BaseModel):
    """웹 UI용 분석 결과"""
    crop_type: str           # 작물 종류
    disease_status: str      # 질병 상태
    confidence: Optional[float] = None  # 신뢰도 (선택적)