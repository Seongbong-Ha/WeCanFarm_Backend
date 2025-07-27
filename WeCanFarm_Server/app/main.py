import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import analyze, admin, auth

# FastAPI 앱 생성
app = FastAPI(
    title="WeCanFarm API",
    description="농작물 질병 분석 API 서버",
    version="1.0.0",
    docs_url="/api/docs",  # API 문서 경로
    redoc_url="/api/redoc"
)

# CORS 설정 (안드로이드 앱 접근 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포시에는 안드로이드 앱 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(auth.router, prefix="/api")  # tags 제거 (auth.py에서 이미 설정)
app.include_router(admin.router, tags=["admin"])  # prefix 제거

# 메인 페이지 - 관리자 대시보드로 리다이렉트
@app.get("/", tags=["redirect"])
async def root():
    """메인 페이지 - 관리자 대시보드로 리다이렉트"""
    return RedirectResponse(url="/admin/dashboard")

# 관리자 대시보드만 HTML 응답으로 유지
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# 정적 파일 및 템플릿 (관리자 대시보드용만)
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 기존 admin 리다이렉트는 제거 (중복)

print("✅ WeCanFarm API 서버 초기화 완료")
print("📱 안드로이드 앱 전용 API 서버 모드")
print("📊 관리자 대시보드: /admin/dashboard")
print("📖 API 문서: /api/docs")