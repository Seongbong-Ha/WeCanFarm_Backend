# 🌱 WeCanFarm Backend

농작물 질병 분석 AI 서비스의 백엔드 API 서버입니다.

YOLO 객체 감지와 ResNet 질병 분류 모델을 통합하여 농작물 이미지를 분석하고 질병을 진단합니다.

## 📋 목차

- [기능](#-기능)
- [기술 스택](#-기술-스택)
- [데이터 파이프라인](#-데이터-파이프라인)
- [Airflow 데이터 오케스트레이션](#-airflow-데이터-오케스트레이션)
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
- 🛠️ **Airflow 기반 자동화된 데이터 파이프라인**

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
- **Workflow Orchestration**: Apache Airflow 3.0+
- **Data Pipeline**: PostgreSQL Hook, Python Operators

### DevOps
- **Server**: Uvicorn
- **API Docs**: Swagger UI
- **Environment**: Python 3.8+
- **Containerization**: Docker, Docker Compose

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

## 🛠️ Airflow 데이터 오케스트레이션

### 개요
Apache Airflow를 활용하여 WeCanFarm의 데이터 파이프라인을 자동화하고 모니터링합니다. 일일 통계 수집, 데이터 품질 검증, 성능 모니터링 등의 작업을 스케줄링된 DAG로 관리합니다.

### 주요 DAG 목록

#### 1. 연결 테스트 DAG (`wecanfarm_connection_test`)
- **목적**: WeCanFarm 데이터베이스 연결 및 테이블 상태 확인
- **스케줄**: 수동 실행
- **주요 작업**:
  - PostgreSQL 연결 테스트
  - 기본 테이블 존재 확인 (users, analysis_requests, analysis_results)
  - 테이블별 레코드 수 조회
  - 데이터베이스 버전 확인

#### 2. 일일 통계 수집 DAG (`wecanfarm_daily_stats`)
- **목적**: 일일 서비스 이용 통계 자동 수집 및 리포트 생성
- **스케줄**: 매일 오전 9시 (KST)
- **주요 작업**:
  - 신규 가입자 수 집계
  - 일일 분석 요청 건수 계산
  - 분석 성공률 산출
  - 누적 사용자 통계 업데이트
  - 요약 리포트 생성

### Airflow 설정

#### 환경 구성
- **Version**: Apache Airflow 3.0.3
- **Executor**: CeleryExecutor
- **Database**: PostgreSQL 13
- **Message Broker**: Redis
- **Container**: Docker Compose

#### 네트워크 구성
```
WeCanFarm PostgreSQL (port 5432) ←→ Airflow Network (airflow_default)
                ↕
Airflow Scheduler/Worker/WebServer ←→ Airflow PostgreSQL (metadata)
```

#### Connection 설정
- **Connection ID**: `wecanfarm_db`
- **Connection Type**: Postgres
- **Host**: `wecanfarm-postgres` (Docker 내부 네트워크)
- **Database**: `wecanfarm_db`
- **User**: `wecanfarm_user`

### 실행 결과 예시

#### 일일 통계 리포트
```
📊 WeCanFarm 일일 리포트 - 2025-07-30
==================================================
👥 신규 가입자: 2명
📈 분석 요청: 15건
✅ 성공한 분석: 13건
📊 성공률: 86.7%
👥 총 사용자: 25명 (누적)
==================================================
```

### 모니터링 및 알림
- **웹 UI**: http://localhost:8080 (Airflow Dashboard)
- **로그 수집**: 모든 Task 실행 로그 중앙화
- **에러 알림**: Task 실패 시 자동 재시도 및 로깅
- **성능 메트릭**: Task 실행 시간 및 성공률 추적

### Airflow 폴더 구조
```
airflow/
├── docker-compose.yaml        # Airflow 서비스 정의
├── dags/                      # DAG 파일들
│   ├── wecanfarm_connection_test.py
│   └── wecanfarm_daily_stats.py
├── logs/                      # 실행 로그 (gitignore)
├── plugins/                   # 커스텀 플러그인
├── config/                    # 설정 파일
└── .env                       # 환경 변수 (gitignore)
```

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

### 7. Airflow 실행 (선택사항)
```bash
cd airflow

# Airflow 초기화
docker-compose up airflow-init

# Airflow 서비스 실행
docker-compose up -d

# Airflow 웹 UI 접속
# http://localhost:8080 (airflow/airflow)
```

### 8. 접속 확인
- **API 문서**: http://localhost:8000/api/docs
- **관리자 대시보드**: http://localhost:8000/admin/dashboard
- **Airflow 대시보드**: http://localhost:8080 (선택사항)

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
├── airflow/                   # Airflow 데이터 파이프라인
│   ├── docker-compose.yaml    # Airflow 서비스 정의
│   ├── dags/                  # DAG 파일들
│   │   ├── wecanfarm_connection_test.py  # DB 연결 테스트
│   │   └── wecanfarm_daily_stats.py      # 일일 통계 수집
│   ├── logs/                  # 실행 로그 (gitignore)
│   ├── plugins/               # 커스텀 플러그인
│   └── .env                   # Airflow 환경 변수
├── requirements.txt           # Python 의존성
├── .env                      # 환경 변수
├── .gitignore                # Git 제외 파일 목록
└── README.md                 # 프로젝트 문서
```

## 🌟 프로젝트 특징

### 데이터 품질 관리
농작물 이미지 데이터의 특성을 이해하고 일관된 품질을 유지하기 위해 다단계 검증 시스템을 구축했습니다. 질병 분류 결과의 정확성과 신뢰도를 지속적으로 모니터링하며, 사용자별 및 작물별 분석 패턴을 추적하여 서비스 품질을 개선합니다.

### 표준화된 데이터 처리
이미지 전처리부터 최종 결과까지 모든 단계에서 표준화된 프로세스를 적용합니다. 크기, 포맷, 품질이 일관되게 관리되며, 분석 결과는 구조화된 형태로 저장되어 재사용 가능한 데이터 모델을 제공합니다.

### 통합 파이프라인
기존의 분절된 이미지 분석 과정을 하나의 통합 파이프라인으로 구성하여 효율성을 극대화했습니다. 일회성 분석에서 벗어나 체계적인 데이터 축적이 가능하며, 파편화된 분석 정보를 통합 대시보드를 통해 한눈에 파악할 수 있습니다.

### 자동화된 데이터 오케스트레이션
Apache Airflow를 통해 데이터 수집, 처리, 분석의 전 과정을 자동화했습니다. 스케줄링된 워크플로우로 일관된 데이터 품질을 유지하며, 실시간 모니터링과 알림 시스템으로 안정적인 서비스 운영을 보장합니다. Analyst Engineer 관점에서 데이터 파이프라인의 투명성과 추적 가능성을 확보했습니다.