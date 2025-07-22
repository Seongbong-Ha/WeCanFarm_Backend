from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

# FastAPI의 인스턴스를 생성
app = FastAPI()

templates = Jinja2Templates(directory="templates")

# templates 폴더의 "index.html" 응답
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 사용자가 폼을 통해 보낸 데이터(content)를 받아서 "result.html" 템플릿에 넘김
@app.post("/result", response_class=HTMLResponse)
async def post_result(request: Request, content: str = Form(...)):
    return templates.TemplateResponse("result.html", {"request": request, "content": content})
