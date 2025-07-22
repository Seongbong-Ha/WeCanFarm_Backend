from fastapi import APIRouter, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import base64
from PIL import Image
from io import BytesIO
import os
from ..services.inference import run_resnet_inference

router = APIRouter()

# ✅ 절대 경로로 templates 디렉토리 지정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.abspath(os.path.join(BASE_DIR, "../templates"))
templates = Jinja2Templates(directory=TEMPLATE_DIR)

@router.get("/", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/analyze_web", response_class=HTMLResponse)
async def analyze_web(request: Request, file: UploadFile = File(...)):
    contents = await file.read()
    image = Image.open(BytesIO(contents))

    result = run_resnet_inference(image)

    # 이미지 → base64 변환
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    encoded_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return templates.TemplateResponse("result.html", {
        "request": request,
        "image_base64": encoded_image,
        "result": result
    })
