# 🌱 WeCanFarm Backend

농작물 질병 분석 AI 서비스의 백엔드 API 서버입니다.

YOLO 객체 감지와 ResNet 질병 분류 모델을 통합하여 농작물 이미지를 분석하고 질병을 진단합니다.

## 📋 목차

- [기능](#-기능)
- [기술 스택](#-기술-스택)
- [데이터 파이프라인](#-데이터-파이프라인)
- [설치 및 실행](#-설치-및-실행)
- [API 문서](#-api-문서)
- [프로젝트 구조](#-프로젝트-구조)
- [프로젝트 특징](#-프로젝트-특징)

## ✨ 기능

- 🔐 **JWT 기반 사용자 인증**
- 🖼️ **이미지 기반 작물 질병 분석**
- 🎯 **YOLO + ResNet 통합 파이프라인**
- 📊 **실시간 관리자 대시보드**
- 💾 **분석 결과 데이터베이스 저장 및 데이터 마트 구축**
- 📱 **Android 앱 연동 지원**
- 🔄 **재사용 가능한 데이터 모델 제공**

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

### Data Engineering
- **Data Processing**: Python
- **Data Validation**: SQLAlchemy ORM
- **Performance Monitoring**: 분석 요청/결과 추적
- **Data Quality**: 이미지 유효성 검사 및 전처리

### DevOps
- **Server**: Uvicorn
- **API Docs**: Swagger UI
- **Environment**: Python 3.8+

## 🔄 데이터 파이프라인

### 데이터 흐름
```
원본 이미지 → 이미지 검증 → YOLO 객체 감지 → ResNet 질병 분류 → 결과 저장 → 데이터 마트
```

### 데이터 변환 과정
1. **원천 데이터**: 사용자가 업로드한 농작물 이미지
2. **정제 및 표준화**: 
   - 이미지 포맷 변환 (RGB)
   - 크기 정규화 (224x224)
   - Base64 인코딩/디코딩
3. **데이터 마트**: 
   - 분석 요청/결과 통계
   - 작물별/질병별 감지 현황
   - 사용자별 분석 이력

### 데이터 검증
- 이미지 유효성 검사 (크기, 포맷, 품질)
- 모델 예측 신뢰도 임계값 적용
- 분석 결과 일관성 검증

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
  "username": "testuser", 
  "email": "test@example.com",
  "password": "password123",
  "full_name": "Test User",
  "role": "USER"  // "USER" 또는 "FARMER"
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
  "access_token": "eyJ...",
  "token_type": "bearer", 
  "user_id": 1,
  "username": "testuser",
  "role": "USER"  // 사용자 역할 정보
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
│   │   └── admin.py           # 관리자 API (데이터 마트)
│   ├── services/              # 비즈니스 로직
│   │   ├── model_manager.py   # AI 모델 관리
│   │   ├── inference.py       # 추론 로직
│   │   └── pipeline.py        # 분석 파이프라인 (데이터 변환)
│   ├── utils/                 # 유틸리티
│   │   └── image_handler.py   # 이미지 처리 및 검증
│   ├── database/              # 데이터베이스
│   │   ├── models.py          # DB 모델 정의 (데이터 마트 스키마)
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
│       └── admin_dashboard.html # 데이터 마트 시각화
├── requirements.txt           # Python 의존성
├── .env                      # 환경 변수
└── README.md                 # 프로젝트 문서
```

## 🌟 프로젝트 특징

### 데이터 품질 관리
농작물 이미지 데이터의 특성을 이해하고 일관된 품질을 유지하기 위해 다단계 검증 시스템을 구축했습니다. 질병 분류 결과의 정확성과 신뢰도를 지속적으로 모니터링하며, 사용자별 및 작물별 분석 패턴을 추적하여 서비스 품질을 개선합니다.

### 표준화된 데이터 처리
이미지 전처리부터 최종 결과까지 모든 단계에서 표준화된 프로세스를 적용합니다. 크기, 포맷, 품질이 일관되게 관리되며, 분석 결과는 구조화된 형태로 저장되어 재사용 가능한 데이터 모델을 제공합니다.

### 통합 파이프라인
기존의 분절된 이미지 분석 과정을 하나의 통합 파이프라인으로 구성하여 효율성을 극대화했습니다. 일회성 분석에서 벗어나 체계적인 데이터 축적이 가능하며, 파편화된 분석 정보를 통합 대시보드를 통해 한눈에 파악할 수 있습니다.