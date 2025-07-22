from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from .routers import analyze
import os

# FastAPI의 인스턴스를 생성
app = FastAPI()
app.include_router(analyze.router)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# templates 폴더의 "index.html" 응답
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 사용자가 폼을 통해 보낸 데이터(content)를 받아서 "result.html" 템플릿에 넘김
@app.post("/result", response_class=HTMLResponse)
async def post_result(request: Request, content: str = Form(...)):
    return templates.TemplateResponse("result.html", {"request": request, "content": content})
