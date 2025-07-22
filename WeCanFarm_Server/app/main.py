import os
from fastapi import FastAPI,Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from .routers import analyze, webanalyze

app = FastAPI()
app.include_router(analyze.router)
app.include_router(webanalyze.router)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# ✅ 경로 로그로 확인
print("📁 TEMPLATE_DIR:", TEMPLATE_DIR)
print("📄 index.html 존재 여부:", os.path.exists(os.path.join(TEMPLATE_DIR, "index.html")))

templates = Jinja2Templates(directory=TEMPLATE_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ✅ result.html 페이지
@app.post("/result", response_class=HTMLResponse)
async def post_result(request: Request, content: str = Form(...)):
    return templates.TemplateResponse("result.html", {"request": request, "content": content})

print("📁 현재 BASE_DIR:", BASE_DIR)
print("📁 TEMPLATE_DIR:", TEMPLATE_DIR)
print("📁 존재 여부:", os.path.exists(TEMPLATE_DIR))
print("📄 index.html 존재 여부:", os.path.exists(os.path.join(TEMPLATE_DIR, "index.html")))
