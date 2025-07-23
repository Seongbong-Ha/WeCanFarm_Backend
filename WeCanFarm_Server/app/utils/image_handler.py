# base64 디코딩
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import List

def decode_base64_to_image(base64_str: str) -> Image.Image:
    # "data:image/jpeg;base64,..." 같은 접두어 제거
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]
    image_data = base64.b64decode(base64_str)
    return Image.open(BytesIO(image_data))
    
def crop_image(image: Image.Image, bbox: List[int]) -> Image.Image:
    """바운딩박스로 이미지 크롭"""
    
def draw_bounding_boxes(image: Image.Image, detections) -> Image.Image:
    """이미지에 바운딩박스 + 라벨 그리기"""

def image_to_base64(image: Image.Image) -> str:
    """이미지를 base64로 인코딩"""