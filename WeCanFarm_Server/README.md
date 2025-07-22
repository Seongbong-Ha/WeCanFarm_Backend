# 🌱 WeCanFram_Server

작물의 병해 여부를 분석하는 AI 기반 위캔팜 프로젝트의 백엔드 서버입니다.  
FastAPI를 기반으로 이미지 업로드, 모델 추론, 결과 반환 기능을 제공합니다.


---

## 🚀 실행 방법

### 1. 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python -m venv SVenv

# 가상환경 활성화
# Windows
SVenv\Scripts\activate
# Mac/Linux
source SVenv/bin/activate


# 패키지 설치
pip install -r requirements.txt

# fastAPI 서버 실행
uvicorn main:app --reload
→ http://127.0.0.1:8000 접속
→ 이미지 업로드 → AI 모델 추론 결과 확인

