# utils/image_handler.py
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple
import os

def decode_base64_to_image(base64_str: str) -> Image.Image:
    """base64 문자열을 PIL Image로 디코딩"""
    # "data:image/jpeg;base64,..." 같은 접두어 제거
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]
    image_data = base64.b64decode(base64_str)
    return Image.open(BytesIO(image_data))

def image_to_base64(image: Image.Image, format: str = "JPEG") -> str:
    """PIL Image를 base64 문자열로 인코딩"""
    buffered = BytesIO()
    # PNG가 아닌 경우 RGB로 변환 (JPEG는 RGBA 지원 안함)
    if format.upper() == "JPEG" and image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.save(buffered, format=format)
    encoded_string = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return encoded_string

def crop_image(image: Image.Image, bbox: List[int]) -> Image.Image:
    """바운딩박스로 이미지 크롭
    Args:
        image: 원본 이미지
        bbox: [x1, y1, x2, y2] 형태의 바운딩박스 좌표
    Returns:
        크롭된 이미지
    """
    x1, y1, x2, y2 = bbox
    # 좌표가 이미지 범위를 벗어나지 않도록 클리핑
    width, height = image.size
    x1 = max(0, min(x1, width))
    y1 = max(0, min(y1, height))
    x2 = max(0, min(x2, width))
    y2 = max(0, min(y2, height))
    
    return image.crop((x1, y1, x2, y2))

def draw_bounding_boxes(image: Image.Image, detections: List[dict], font_size: int = 20) -> Image.Image:
    """이미지에 바운딩박스와 라벨을 그리기
    Args:
        image: 원본 이미지
        detections: 감지 결과 리스트
            [{"bbox": [x1, y1, x2, y2], "label": "질병명", "confidence": 0.95, "crop_type": "pepper"}]
        font_size: 텍스트 폰트 크기
    Returns:
        바운딩박스가 그려진 이미지
    """
    # 이미지 복사 (원본 보존)
    image_with_boxes = image.copy()
    draw = ImageDraw.Draw(image_with_boxes)
    
    # 폰트 설정 (시스템 기본 폰트 사용)
    try:
        # macOS의 경우
        font_path = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
        else:
            # 기본 폰트 사용
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # 색상 팔레트 (작물/질병별로 다른 색상)
    color_palette = {
        "정상": "#00FF00",          # 초록색
        "고추점무늬병": "#FF0000",    # 빨간색
        "고추마일드모틀바이러스": "#FF8800",  # 주황색
        "default": "#0080FF"       # 파란색 (기본)
    }
    
    for detection in detections:
        bbox = detection.get("bbox", [])
        label = detection.get("label", "알 수 없음")
        confidence = detection.get("confidence", 0.0)
        
        if len(bbox) != 4:
            continue
            
        x1, y1, x2, y2 = bbox
        
        # 바운딩박스 색상 선택
        color = color_palette.get(label, color_palette["default"])
        
        # 바운딩박스 그리기 (두께 3픽셀)
        for i in range(3):
            draw.rectangle([x1-i, y1-i, x2+i, y2+i], outline=color)
        
        # 라벨 텍스트 생성
        text = f"{label} ({confidence:.2f})"
        
        # 텍스트 배경 박스 크기 계산
        bbox_text = draw.textbbox((0, 0), text, font=font)
        text_width = bbox_text[2] - bbox_text[0]
        text_height = bbox_text[3] - bbox_text[1]
        
        # 텍스트 배경 그리기
        text_bg_coords = [x1, y1 - text_height - 4, x1 + text_width + 8, y1]
        draw.rectangle(text_bg_coords, fill=color)
        
        # 텍스트 그리기 (흰색)
        draw.text((x1 + 4, y1 - text_height - 2), text, fill="white", font=font)
    
    return image_with_boxes

def resize_image(image: Image.Image, max_size: Tuple[int, int] = (1024, 1024), 
                maintain_aspect: bool = True) -> Image.Image:
    """이미지 크기 조정
    Args:
        image: 원본 이미지
        max_size: 최대 크기 (width, height)
        maintain_aspect: 종횡비 유지 여부
    Returns:
        크기가 조정된 이미지
    """
    if maintain_aspect:
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        return image
    else:
        return image.resize(max_size, Image.Resampling.LANCZOS)

def validate_image(image: Image.Image) -> bool:
    """이미지 유효성 검사
    Args:
        image: 검사할 이미지
    Returns:
        유효한 이미지인지 여부
    """
    try:
        # 기본 검사
        if image is None:
            return False
        
        # 크기 검사 (최소 32x32)
        width, height = image.size
        if width < 32 or height < 32:
            return False
        
        # 최대 크기 검사 (4096x4096)
        if width > 4096 or height > 4096:
            return False
        
        # 이미지 모드 검사
        if image.mode not in ["RGB", "RGBA", "L"]:
            return False
        
        return True
        
    except Exception as e:
        print(f"이미지 유효성 검사 실패: {e}")
        return False

def prepare_image_for_model(image: Image.Image, target_size: Tuple[int, int] = (224, 224)) -> Image.Image:
    """모델 입력용 이미지 전처리
    Args:
        image: 원본 이미지
        target_size: 목표 크기
    Returns:
        전처리된 이미지
    """
    # RGB로 변환
    if image.mode != "RGB":
        image = image.convert("RGB")
    
    # 크기 조정
    image = image.resize(target_size, Image.Resampling.LANCZOS)
    
    return image

# YOLO 통합을 위한 Mock 함수 (실제 YOLO 모델 완성 시 교체)
def mock_yolo_detection(image: Image.Image) -> List[dict]:
    """YOLO 완성 전까지 사용할 더미 감지 함수
    Args:
        image: 입력 이미지
    Returns:
        더미 감지 결과
    """
    width, height = image.size
    
    # 더미 바운딩박스 생성 (이미지 크기에 비례)
    mock_detections = [
        {
            "bbox": [int(width*0.2), int(height*0.2), int(width*0.6), int(height*0.7)],
            "crop_type": "pepper",
            "confidence": 0.85
        },
        {
            "bbox": [int(width*0.5), int(height*0.1), int(width*0.9), int(height*0.5)],
            "crop_type": "pepper", 
            "confidence": 0.72
        }
    ]
    
    return mock_detections