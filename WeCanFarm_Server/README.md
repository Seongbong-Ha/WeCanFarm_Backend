# 🌱 WeCanFarm Server

> **농작물 질병 AI 분석 서비스**  
> YOLO 객체 감지와 ResNet 질병 분류를 결합한 스마트 농업 솔루션

## 📋 목차

- [프로젝트 개요](#-프로젝트-개요)
- [주요 기능](#-주요-기능)
- [기술 스택](#-기술-스택)
- [시스템 아키텍처](#-시스템-아키텍처)
- [설치 및 실행](#-설치-및-실행)
- [API 문서](#-api-문서)
- [프로젝트 구조](#-프로젝트-구조)
- [사용법](#-사용법)
- [개발 가이드](#-개발-가이드)

## 🎯 프로젝트 개요

WeCanFarm은 농작물 이미지를 분석하여 질병을 자동으로 진단하는 AI 기반 서비스입니다. 농부들이 스마트폰으로 작물 사진을 찍으면, AI가 질병을 감지하고 진단 결과를 제공합니다.

### 🔬 AI 모델 파이프라인

1. **YOLO v8**: 이미지에서 작물 객체를 감지하고 위치를 파악
2. **ResNet**: 감지된 작물 영역의 질병을 분류 및 진단
3. **결과 시각화**: 바운딩 박스와 질병 정보를 오버레이

## ✨ 주요 기능

### 🔍 **이미지 분석**
- **전체 파이프라인**: YOLO 객체 감지 + ResNet 질병 분류
- **단일 분석**: ResNet을 사용한 직접 질병 분류
- **다중 객체 지원**: 한 이미지에서 여러 작물 동시 분석

### 🌐 **웹 인터페이스**
- 직관적인 이미지 업로드 UI
- 실시간 분석 결과 표시
- 분석 방식 선택 (전체/단일)

### 📱 **모바일 API**
- RESTful API 엔드포인트
- Base64 이미지 업로드 지원
- JSON 형태의 구조화된 응답

### 👨‍💼 **관리자 대시보드**
- 실시간 서비스 통계
- 사용자 및 분석 현황
- 질병별/작물별 분석 데이터

## 🛠 기술 스택

### **Backend**
- **FastAPI**: 고성능 웹 프레임워크
- **Pydantic**: 데이터 검증 및 직렬화
- **SQLAlchemy**: ORM 및 데이터베이스 관리

### **AI/ML**
- **TensorFlow/Keras**: 딥러닝 모델 추론
- **Ultralytics YOLO**: 객체 감지
- **PIL/OpenCV**: 이미지 처리

### **Frontend**
- **Jinja2**: 서버사이드 템플릿
- **HTML/CSS/JavaScript**: 웹 UI
- **Chart.js**: 데이터 시각화

### **Database**
- **SQLite/PostgreSQL**: 데이터 저장
- **Alembic**: 데이터베이스 마이그레이션

## 🏗 시스템 아키텍처

```
🌐 External Interface (웹/모바일/관리자)
         ↓
🚀 FastAPI Application (main.py)
         ↓
🛣️ Router Layer (webanalyze, analyze, admin)
         ↓
⚙️ Service Layer (pipeline, inference, model_manager)
         ↓
🛠️ Utility Layer (image_handler) + 🤖 AI Models (YOLO, ResNet)
         ↓
🗄️ Data Layer (database, schemas)
```

## 🚀 설치 및 실행

### **1. 환경 요구사항**
- Python 3.8+
- CUDA (GPU 사용 시)
- 8GB+ RAM 권장

### **2. 프로젝트 클론**
```bash
git clone https://github.com/your-repo/WeCanFarm_Server.git
cd WeCanFarm_Server
```

### **3. 가상환경 설정**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### **4. 의존성 설치**
```bash
pip install -r requirements.txt
```

### **5. AI 모델 다운로드**
```bash
# 모델 파일을 app/models/ 디렉토리에 배치
mkdir -p app/models
# yolo_v1.pt, pepper_disease_model.keras 파일 복사
```

### **6. 데이터베이스 초기화**
```bash
alembic upgrade head
```

### **7. 서버 실행**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **8. 접속 확인**
- 웹 UI: http://localhost:8000
- API 문서: http://localhost:8000/docs
- 관리자: http://localhost:8000/admin

## 📚 API 문서

### **전체 파이프라인 분석**
```http
POST /analyze
Content-Type: application/json

{
  "image_base64": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**응답:**
```json
{
  "image_base64": "결과_이미지_base64",
  "detections": [
    {
      "bbox": [x1, y1, x2, y2],
      "crop_type": "pepper",
      "disease_status": "고추점무늬병",
      "disease_confidence": 0.92,
      "yolo_confidence": 0.85,
      "label": "pepper: 고추점무늬병"
    }
  ],
  "total_detections": 1
}
```

### **단일 작물 분석**
```http
POST /analyze_single?crop_type=pepper
Content-Type: application/json

{
  "image_base64": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**응답:**
```json
{
  "crop_type": "pepper",
  "disease_status": "정상",
  "confidence": 0.94
}
```

## 📁 프로젝트 구조

```
WeCanFarm_Server/
├── app/
│   ├── main.py                 # FastAPI 메인 애플리케이션
│   ├── routers/               # API 라우터
│   │   ├── analyze.py         # 분석 API
│   │   ├── webanalyze.py      # 웹 UI 라우터
│   │   └── admin.py           # 관리자 라우터
│   ├── services/              # 비즈니스 로직
│   │   ├── pipeline.py        # 이미지 처리 파이프라인
│   │   ├── inference.py       # AI 모델 추론
│   │   └── model_manager.py   # 모델 관리
│   ├── utils/                 # 유틸리티
│   │   └── image_handler.py   # 이미지 처리 도구
│   ├── database/              # 데이터베이스
│   │   ├── models.py          # ORM 모델
│   │   └── database.py        # DB 연결
│   ├── schemas/               # 데이터 스키마
│   │   └── request_response.py
│   ├── templates/             # HTML 템플릿
│   │   ├── index.html
│   │   ├── pipeline_result.html
│   │   ├── single_result.html
│   │   ├── error.html
│   │   └── admin_dashboard.html
│   ├── models/                # AI 모델 파일
│   │   ├── yolo_v1.pt
│   │   └── pepper_disease_model.keras
│   └── static/                # 정적 파일
├── requirements.txt           # Python 의존성
├── alembic.ini               # DB 마이그레이션 설정
└── README.md                 # 프로젝트 문서
```

## 💡 사용법

### **웹 브라우저에서**
1. http://localhost:8000 접속
2. 작물 이미지 업로드
3. 분석 방식 선택 (전체 파이프라인/단일 분석)
4. 결과 확인

### **모바일 앱에서**
1. 이미지를 Base64로 인코딩
2. `/analyze` 또는 `/analyze_single` API 호출
3. JSON 응답 파싱하여 결과 표시

### **관리자로서**
1. http://localhost:8000/admin 접속
2. 실시간 서비스 통계 확인
3. 사용자 및 분석 현황 모니터링

## 🔧 개발 가이드

### **새로운 작물 모델 추가**

1. **모델 파일 추가**
   ```bash
   # app/models/에 새 모델 파일 배치
   cp tomato_disease_model.keras app/models/
   ```

2. **ModelManager 업데이트**
   ```python
   # app/services/model_manager.py
   def _load_tomato_model(self):
       """토마토 모델 로드"""
       model_path = os.path.join(os.path.dirname(__file__), '../models/tomato_disease_model.keras')
       # ... 모델 로딩 로직
   ```

3. **클래스 라벨 정의**
   ```python
   self.class_labels['tomato'] = {
       0: "early_blight",
       1: "late_blight",
       2: "normal"
   }
   ```

### **새로운 API 엔드포인트 추가**

1. **라우터 생성**
   ```python
   # app/routers/new_feature.py
   from fastapi import APIRouter
   router = APIRouter(prefix="/new_feature")
   
   @router.get("/endpoint")
   async def new_endpoint():
       return {"message": "Hello World"}
   ```

2. **메인 앱에 등록**
   ```python
   # app/main.py
   from .routers import new_feature
   app.include_router(new_feature.router)
   ```

### **데이터베이스 스키마 변경**

1. **모델 수정**
   ```python
   # app/database/models.py에서 모델 수정
   ```

2. **마이그레이션 생성**
   ```bash
   alembic revision --autogenerate -m "Add new column"
   ```

3. **마이그레이션 적용**
   ```bash
   alembic upgrade head
   ```

### **테스트 실행**

```bash
# 단위 테스트
pytest tests/

# 특정 테스트
pytest tests/test_inference.py

# 커버리지 측정
pytest --cov=app tests/
```

### **코드 품질 검사**

```bash
# 코드 포맷팅
black app/

# 린팅
flake8 app/

# 타입 체크
mypy app/
```

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 지원 및 문의

- **이슈 리포트**: [GitHub Issues](https://github.com/your-repo/WeCanFarm_Server/issues)
- **이메일**: support@wecanfarm.com
- **문서**: [Wiki](https://github.com/your-repo/WeCanFarm_Server/wiki)

## 🏆 크레딧

- **AI 모델**: YOLOv8 (Ultralytics), ResNet (TensorFlow)
- **웹 프레임워크**: FastAPI
- **개발팀**: WeCanFarm Team

---

**Made with ❤️ by WeCanFarm Team**