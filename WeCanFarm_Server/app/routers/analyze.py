from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session
import json
import time
from datetime import datetime

from ..schemas.request_response import (
    AnalyzeRequest, 
    AnalyzeResponse, 
    SingleAnalyzeResponse,
    DetectionResult
)
from ..utils.image_handler import decode_base64_to_image, image_to_base64
from ..services.pipeline import process_image_pipeline, process_single_crop_analysis
from ..database.database import get_db
from ..database.models import (
    AnalysisRequest as DBAnalysisRequest, 
    AnalysisResult as DBAnalysisResult,
    AnalysisType, 
    RequestStatus,
    AnalysisRequestCRUD,
    AnalysisResultCRUD,
    User
)
# JWT 인증 import (routers/auth.py에서 가져오기)
from .auth import get_current_user

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(
    req: AnalyzeRequest,
    request: Request,  # Request 추가 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    print("🔍 [AUTH DEBUG] === 인증 디버깅 시작 ===")
    print(f"🔍 [AUTH DEBUG] Authorization 헤더: {request.headers.get('authorization', 'NONE')}")
    print(f"🔍 [AUTH DEBUG] 현재 사용자: {current_user.username if current_user else 'NONE'}")
    print(f"🔍 [AUTH DEBUG] 사용자 ID: {current_user.id if current_user else 'NONE'}")
    print("🔍 [AUTH DEBUG] === 디버깅 끝 ===")
    
    """
    이미지 분석 API (전체 파이프라인) - JWT 인증 버전
    - YOLO 객체 감지 → ResNet 질병 분류 → 결과 시각화 → DB 저장
    """
    start_time = time.time()
    
    try:
        print("=" * 50)
        print(f"🔍 [DEBUG] 새로운 analyze 요청 - 사용자: {current_user.username} (ID: {current_user.id})")
        
        # 1. 이미지 디코딩
        try:
            image = decode_base64_to_image(req.image_base64)
            print(f"✅ [DEBUG] 이미지 변환 성공 - 크기: {image.size}")
        except Exception as e:
            print(f"❌ [DEBUG] 이미지 디코딩 실패: {e}")
            raise HTTPException(status_code=400, detail=f"이미지 디코딩 실패: {str(e)}")

        # 2. DB에 분석 요청 저장 (실제 사용자 ID 사용)
        try:
            temp_image_url = f"user_{current_user.id}_image_{int(time.time())}.jpg"
            
            db_request = AnalysisRequestCRUD.create(
                db=db,
                user_id=current_user.id,
                image_url=temp_image_url,
                analysis_type=AnalysisType.PIPELINE
            )
            print(f"✅ [DEBUG] DB 요청 저장 완료 - Request ID: {db_request.id}, User: {current_user.username}")
            
        except Exception as e:
            print(f"❌ [DEBUG] DB 요청 저장 실패: {e}")
            raise HTTPException(status_code=500, detail=f"분석 요청 저장 실패: {str(e)}")

        # 3. 요청 상태를 PROCESSING으로 변경
        try:
            AnalysisRequestCRUD.update_status(db, db_request.id, RequestStatus.PROCESSING)
            print("📊 [DEBUG] 상태 변경: PENDING → PROCESSING")
        except Exception as e:
            print(f"⚠️ [DEBUG] 상태 업데이트 실패: {e}")

        # 4. 파이프라인 실행
        try:
            result = process_image_pipeline(image)
            print(f"✅ [DEBUG] 파이프라인 실행 완료: {result['processing_status']}")
        except Exception as e:
            AnalysisRequestCRUD.update_status(db, db_request.id, RequestStatus.FAILED)
            print(f"❌ [DEBUG] 파이프라인 실행 실패: {e}")
            raise HTTPException(status_code=500, detail=f"파이프라인 실행 실패: {str(e)}")

        # 5. 처리 시간 계산
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # 6. 처리 결과에 따라 DB 업데이트
        if result["processing_status"] == "성공":
            try:
                db_result = AnalysisResultCRUD.create(
                    db=db,
                    request_id=db_request.id,
                    total_detections=result["total_detections"],
                    result_image_url=f"user_{current_user.id}_result_{db_request.id}.jpg",
                    detection_data=result["detections"],
                    processing_status=result["processing_status"]
                )
                
                AnalysisRequestCRUD.update_status(
                    db, db_request.id, RequestStatus.COMPLETED, processing_time_ms
                )
                
                print(f"✅ [DEBUG] DB 결과 저장 완료 - Result ID: {db_result.id}")
                print(f"⏱️ [DEBUG] 처리 시간: {processing_time_ms}ms")
                
            except Exception as e:
                print(f"❌ [DEBUG] 결과 저장 실패: {e}")
                AnalysisRequestCRUD.update_status(db, db_request.id, RequestStatus.FAILED)
        else:
            AnalysisRequestCRUD.update_status(
                db, db_request.id, RequestStatus.FAILED, processing_time_ms
            )
            print(f"❌ [DEBUG] 파이프라인 처리 실패: {result['processing_status']}")

        # 7. API 응답 생성
        try:
            response = AnalyzeResponse(
                image_base64=result["image_base64"],
                detections=result["detections"],
                total_detections=result["total_detections"]
            )
            print(f"✅ [DEBUG] API 응답 생성 성공 - 사용자: {current_user.username}")
            print("=" * 50)
            return response
            
        except Exception as e:
            print(f"❌ [DEBUG] 응답 생성 실패: {e}")
            raise HTTPException(status_code=500, detail=f"응답 생성 실패: {str(e)}")

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ [DEBUG] 예상치 못한 오류: {e}")
        if 'db_request' in locals():
            try:
                AnalysisRequestCRUD.update_status(db, db_request.id, RequestStatus.FAILED)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"서버 내부 오류: {str(e)}")

@router.post("/analyze_single", response_model=SingleAnalyzeResponse)
async def analyze_single_crop(
    req: AnalyzeRequest, 
    crop_type: str = "pepper", 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    단일 작물 분석 API (기존 방식) - JWT 인증 버전
    - YOLO 없이 ResNet으로 직접 분석 → DB 저장
    """
    start_time = time.time()
    
    try:
        print("=" * 50)
        print(f"🔍 [DEBUG] 새로운 analyze_single 요청 - 사용자: {current_user.username}, crop_type: {crop_type}")
        
        # 1. 이미지 디코딩
        try:
            image = decode_base64_to_image(req.image_base64)
            print(f"✅ [DEBUG] 이미지 변환 성공: {image.size}")
        except Exception as e:
            print(f"❌ [DEBUG] 이미지 디코딩 실패: {e}")
            raise HTTPException(status_code=400, detail=f"이미지 디코딩 실패: {str(e)}")

        # 2. DB에 분석 요청 저장
        try:
            temp_image_url = f"user_{current_user.id}_single_{int(time.time())}.jpg"
            db_request = AnalysisRequestCRUD.create(
                db=db,
                user_id=current_user.id,
                image_url=temp_image_url,
                analysis_type=AnalysisType.SINGLE
            )
            print(f"✅ [DEBUG] DB 요청 저장 완료 - Request ID: {db_request.id}, User: {current_user.username}")
        except Exception as e:
            print(f"❌ [DEBUG] DB 요청 저장 실패: {e}")
            raise HTTPException(status_code=500, detail=f"분석 요청 저장 실패: {str(e)}")

        # 3. 상태를 PROCESSING으로 변경
        AnalysisRequestCRUD.update_status(db, db_request.id, RequestStatus.PROCESSING)

        # 4. 단일 작물 분석
        try:
            result = process_single_crop_analysis(image, crop_type)
            print(f"✅ [DEBUG] 단일 분석 완료: {result.get('disease_status', 'unknown')}")
        except Exception as e:
            AnalysisRequestCRUD.update_status(db, db_request.id, RequestStatus.FAILED)
            print(f"❌ [DEBUG] 단일 분석 실패: {e}")
            raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")

        # 5. 처리 시간 계산
        processing_time_ms = int((time.time() - start_time) * 1000)

        # 6. 결과 처리
        if not result["disease_status"].startswith(("분석 실패", "이미지 유효성")):
            try:
                single_detection_data = [{
                    "crop_type": result["crop_type"],
                    "disease_status": result["disease_status"],
                    "confidence": result.get("confidence", 0.0),
                    "analysis_type": "single",
                    "user_id": current_user.id
                }]
                
                db_result = AnalysisResultCRUD.create(
                    db=db,
                    request_id=db_request.id,
                    total_detections=1,
                    result_image_url=f"user_{current_user.id}_single_result_{db_request.id}.jpg",
                    detection_data=single_detection_data,
                    processing_status="성공"
                )
                
                AnalysisRequestCRUD.update_status(
                    db, db_request.id, RequestStatus.COMPLETED, processing_time_ms
                )
                
                print(f"✅ [DEBUG] 단일 분석 결과 저장 완료 - 사용자: {current_user.username}")
                
            except Exception as e:
                print(f"❌ [DEBUG] 결과 저장 실패: {e}")
                AnalysisRequestCRUD.update_status(db, db_request.id, RequestStatus.FAILED)
        else:
            AnalysisRequestCRUD.update_status(
                db, db_request.id, RequestStatus.FAILED, processing_time_ms
            )
            print(f"❌ [DEBUG] 분석 결과 오류: {result['disease_status']}")
            raise HTTPException(status_code=500, detail=result["disease_status"])

        print(f"✅ [DEBUG] analyze_single 완료 - 사용자: {current_user.username}")
        print("=" * 50)
        
        # 7. 응답 반환
        return {
            "crop_type": result["crop_type"],
            "disease_status": result["disease_status"],
            "confidence": result.get("confidence", 0.0)
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ [DEBUG] 예상치 못한 오류: {e}")
        if 'db_request' in locals():
            try:
                AnalysisRequestCRUD.update_status(db, db_request.id, RequestStatus.FAILED)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"서버 내부 오류: {str(e)}")