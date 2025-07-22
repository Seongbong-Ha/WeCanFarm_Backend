# base64 디코딩
import base64
from io import BytesIO
from PIL import Image

def decode_base64_to_image(base64_str: str) -> Image.Image:
    # "data:image/jpeg;base64,..." 같은 접두어 제거
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]
    image_data = base64.b64decode(base64_str)
    return Image.open(BytesIO(image_data))
