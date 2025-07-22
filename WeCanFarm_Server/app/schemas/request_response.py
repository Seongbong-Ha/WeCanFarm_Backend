# 요청/응답 정의
from pydantic import BaseModel
from typing import List

class AnalyzeRequest(BaseModel):
    image_base64: str  # 안드로이드 앱에서 전송된 base64 인코딩 이미지

class DetectionResult(BaseModel):
    bbox: List[int]      # [xtl, ytl, xbr, ybr] 형태의 바운딩 박스
    class_: str          # 예: "정상", "고추점무늬병"

    class Config:
        fields = {'class_': 'class'}  # JSON 필드명으로는 'class' 사용

class AnalyzeResponse(BaseModel):
    result_image_base64: str               # 감지 결과가 표시된 이미지
    detections: List[DetectionResult]      # 감지된 객체 리스트