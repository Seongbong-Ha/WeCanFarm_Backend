# 🌱 WeCanFarm Backend

농작물 질병 분석 AI 서비스의 백엔드 API 서버입니다.

YOLO 객체 감지와 ResNet 질병 분류 모델을 통합하여 농작물 이미지를 분석하고 질병을 진단합니다.

## 📋 목차

- [기능](#-기능)
- [기술 스택](#-기술-스택)
- [설치 및 실행](#-설치-및-실행)
- [API 문서](#-api-문서)
- [프로젝트 구조](#-프로젝트-구조)
- [개발 가이드](#-개발-가이드)

## ✨ 기능

- 🔐 **JWT 기반 사용자 인증**
- 🖼️ **이미지 기반 작물 질병 분석**
- 🎯 **YOLO + ResNet 통합 파이프라인**
- 📊 **실시간 관리자 대시보드**
- 💾 **분석 결과 데이터베이스 저장**
- 📱 **Android 앱 연동 지원**

## 🛠 기술 스택

### Backend
- **Framework**: FastAPI
- **Database**: SQLAlchemy + PostgreSQL/SQLite
- **Authentication**: JWT (PyJWT)
- **Password**: Passlib + bcrypt

### AI/ML
- **Deep Learning**: TensorFlow/Keras
- **Object Detection**: YOLO (Ultralytics)
- **Image Processing**: PIL, OpenCV
- **Models**: 
  - ResNet50 (질병 분류)
  - YOLOv8 (객체 감지)

### DevOps
- **Server**: Uvicorn
- **API Docs**: Swagger UI
- **Environment**: Python 3.8+

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/your-username/WeCanFarm_Backend.git
cd WeCanFarm_Backend
```

### 2. 가상환경 설정
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정
`.env` 파일을 생성하고 다음 내용을 추가:
```env
SECRET_KEY=WeCanFarm_Auth_Key_Production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite:///./wecanfarm.db
```

### 5. 데이터베이스 초기화
```bash
python -m app.database.init_db
```

### 6. 서버 실행
```bash
cd WeCanFarm_Server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. 접속 확인
- **API 문서**: http://localhost:8000/api/docs
- **관리자 대시보드**: http://localhost:8000/admin/dashboard

## 📱 API 문서 (Android Kotlin)

### 📡 기본 정보

- **베이스 URL**: `http://your-server:8000`
- **인증**: JWT Bearer Token
- **Content-Type**: `application/json`

---

### 🔐 인증

#### 회원가입
```http
POST /api/auth/register
```

**Request:**
```json
{
  "username": "string",
  "email": "string", 
  "password": "string",
  "full_name": "string"
}
```

**Response (200):**
```json
{
  "message": "회원가입이 완료되었습니다",
  "user_id": 1
}
```

#### 로그인
```http
POST /api/auth/login
```

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": 1,
  "username": "testuser"
}
```

#### 사용자 정보 조회
```http
GET /api/auth/me
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "user_id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "full_name": "테스트 사용자",
  "role": "USER",
  "is_active": true,
  "created_at": "2025-01-27T10:30:00"
}
```

---

### 🔬 이미지 분석

#### 전체 분석 (YOLO + ResNet)
```http
POST /api/analyze
Authorization: Bearer {token}
```

**Request:**
```json
{
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB..."
}
```

**Response (200):**
```json
{
  "image_base64": "결과_이미지_base64_string",
  "detections": [
    {
      "bbox": [10, 20, 100, 150],
      "crop_type": "pepper",
      "disease_status": "고추점무늬병",
      "disease_confidence": 0.95,
      "yolo_confidence": 0.87,
      "label": "pepper: 고추점무늬병"
    }
  ],
  "total_detections": 1
}
```

#### 단일 분석 (ResNet만)
```http
POST /api/analyze_single?crop_type=pepper
Authorization: Bearer {token}
```

**Request:**
```json
{
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB..."
}
```

**Response (200):**
```json
{
  "crop_type": "pepper",
  "disease_status": "고추점무늬병", 
  "confidence": 0.95
}
```

---

### 📊 HTTP 상태 코드

| 코드 | 의미 | 설명 |
|------|------|------|
| **200** | 성공 | 요청 성공 |
| **400** | 잘못된 요청 | 유효성 검사 실패 |
| **401** | 인증 실패 | 토큰 없음/만료/잘못됨 |
| **500** | 서버 오류 | 내부 서버 오류 |

---
## 📁 프로젝트 구조

```
WeCanFarm_Server/
├── app/
│   ├── main.py                 # FastAPI 앱 설정
│   ├── routers/               # API 라우터
│   │   ├── auth.py            # 인증 관련 API
│   │   ├── analyze.py         # 분석 API
│   │   └── admin.py           # 관리자 API
│   ├── services/              # 비즈니스 로직
│   │   ├── model_manager.py   # AI 모델 관리
│   │   ├── inference.py       # 추론 로직
│   │   └── pipeline.py        # 분석 파이프라인
│   ├── utils/                 # 유틸리티
│   │   └── image_handler.py   # 이미지 처리
│   ├── database/              # 데이터베이스
│   │   ├── models.py          # DB 모델 정의
│   │   └── database.py        # DB 연결 설정
│   ├── schemas/               # Pydantic 스키마
│   │   ├── auth.py            # 인증 스키마
│   │   └── request_response.py # API 스키마
│   ├── auth/                  # 인증 유틸리티
│   │   └── auth.py            # JWT 처리
│   ├── models/                # AI 모델 파일
│   │   ├── pepper_disease_model.keras
│   │   └── yolo_v1.pt
│   └── templates/             # HTML 템플릿
│       └── admin_dashboard.html
├── requirements.txt           # Python 의존성
├── .env                      # 환경 변수
└── README.md                 # 프로젝트 문서
```

## 👨‍💻 개발 가이드

### 새로운 작물 모델 추가

1. **모델 파일 추가**: `app/models/` 디렉토리에 새 모델 파일 배치
2. **ModelManager 수정**: `model_manager.py`에서 새 작물 로딩 함수 추가
3. **클래스 라벨 정의**: 새 작물의 질병 클래스 매핑 추가

```python
# model_manager.py 예시
def _load_tomato_model(self):
    model_path = os.path.join(os.path.dirname(__file__), '../models/tomato_disease_model.keras')
    self.models['tomato'] = tf.keras.models.load_model(model_path)
    
    self.class_labels['tomato'] = {
        0: "healthy",
        1: "early_blight",
        2: "late_blight"
    }
```

### API 엔드포인트 추가

1. **라우터 생성**: `routers/` 디렉토리에 새 라우터 파일 생성
2. **스키마 정의**: `schemas/` 디렉토리에 요청/응답 모델 정의
3. **메인 앱 등록**: `main.py`에서 새 라우터 등록

### 데이터베이스 모델 수정

1. **모델 클래스 수정**: `database/models.py`에서 모델 정의 변경
2. **마이그레이션 실행**: Alembic을 이용한 DB 스키마 변경
3. **CRUD 함수 업데이트**: 새 필드에 대한 CRUD 함수 추가
