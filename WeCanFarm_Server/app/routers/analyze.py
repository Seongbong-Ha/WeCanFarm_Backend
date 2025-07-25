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
    AnalysisResultCRUD
)

router = APIRouter()

# 임시 사용자 ID (나중에 JWT 인증에서 가져올 예정)
TEMP_USER_ID = 1

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(req: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    이미지 분석 API (전체 파이프라인) - DB 연동 버전
    - YOLO 객체 감지 → ResNet 질병 분류 → 결과 시각화 → DB 저장
    """
    start_time = time.time()
    
    try:
        # 🔍 디버깅 로그
        print("=" * 50)
        print("🔍 [DEBUG] 새로운 analyze 요청 받음")
        
        # 1. 이미지 디코딩
        try:
            image = decode_base64_to_image(req.image_base64)
            print(f"✅ [DEBUG] 이미지 변환 성공 - 크기: {image.size}")
        except Exception as e:
            print(f"❌ [DEBUG] 이미지 디코딩 실패: {e}")
            raise HTTPException(status_code=400, detail=f"이미지 디코딩 실패: {str(e)}")

        # 2. DB에 분석 요청 저장 (PENDING 상태)
        try:
            # 임시로 이미지 URL을 base64의 첫 30자로 저장 (나중에 파일 저장 시스템으로 변경)
            temp_image_url = f"temp_image_{int(time.time())}.jpg"
            
            db_request = AnalysisRequestCRUD.create(
                db=db,
                user_id=TEMP_USER_ID,  # 임시 사용자 ID
                image_url=temp_image_url,
                analysis_type=AnalysisType.PIPELINE
            )
            print(f"✅ [DEBUG] DB 요청 저장 완료 - ID: {db_request.id}")
            
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
            # 실패 시 DB 상태 업데이트
            AnalysisRequestCRUD.update_status(db, db_request.id, RequestStatus.FAILED)
            print(f"❌ [DEBUG] 파이프라인 실행 실패: {e}")
            raise HTTPException(status_code=500, detail=f"파이프라인 실행 실패: {str(e)}")

        # 5. 처리 시간 계산
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # 6. 처리 결과에 따라 DB 업데이트
        if result["processing_status"] == "성공":
            try:
                # 성공: 결과 저장
                db_result = AnalysisResultCRUD.create(
                    db=db,
                    request_id=db_request.id,
                    total_detections=result["total_detections"],
                    result_image_url=f"result_{db_request.id}.jpg",  # 임시 URL
                    detection_data=result["detections"],  # JSON으로 저장
                    processing_status=result["processing_status"]
                )
                
                # 요청 상태를 COMPLETED로 변경
                AnalysisRequestCRUD.update_status(
                    db, db_request.id, RequestStatus.COMPLETED, processing_time_ms
                )
                
                print(f"✅ [DEBUG] DB 결과 저장 완료 - Result ID: {db_result.id}")
                print(f"⏱️ [DEBUG] 처리 시간: {processing_time_ms}ms")
                
            except Exception as e:
                print(f"❌ [DEBUG] 결과 저장 실패: {e}")
                # 실패해도 API 응답은 정상적으로 반환
                AnalysisRequestCRUD.update_status(db, db_request.id, RequestStatus.FAILED)
        else:
            # 실패: 상태만 업데이트
            AnalysisRequestCRUD.update_status(
                db, db_request.id, RequestStatus.FAILED, processing_time_ms
            )
            print(f"❌ [DEBUG] 파이프라인 처리 실패: {result['processing_status']}")

        # 7. API 응답 생성 (기존과 동일)
        try:
            response = AnalyzeResponse(
                image_base64=result["image_base64"],
                detections=result["detections"],
                total_detections=result["total_detections"]
            )
            print("✅ [DEBUG] API 응답 생성 성공")
            print("=" * 50)
            return response
            
        except Exception as e:
            print(f"❌ [DEBUG] 응답 생성 실패: {e}")
            raise HTTPException(status_code=500, detail=f"응답 생성 실패: {str(e)}")

    except HTTPException as he:
        # HTTPException은 그대로 재발생
        raise he
    except Exception as e:
        # 예상치 못한 오류 처리
        print(f"❌ [DEBUG] 예상치 못한 오류: {e}")
        if 'db_request' in locals():
            try:
                AnalysisRequestCRUD.update_status(db, db_request.id, RequestStatus.FAILED)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"서버 내부 오류: {str(e)}")

@router.post("/analyze_single", response_model=SingleAnalyzeResponse)
async def analyze_single_crop(req: AnalyzeRequest, crop_type: str = "pepper", db: Session = Depends(get_db)):
    """
    단일 작물 분석 API (기존 방식) - DB 연동 버전
    - YOLO 없이 ResNet으로 직접 분석 → DB 저장
    """
    start_time = time.time()
    
    try:
        print("=" * 50)
        print("🔍 [DEBUG] 새로운 analyze_single 요청 받음")
        print(f"🔍 [DEBUG] crop_type: {crop_type}")
        
        # 1. 이미지 디코딩
        try:
            image = decode_base64_to_image(req.image_base64)
            print(f"✅ [DEBUG] 이미지 변환 성공: {image.size}")
        except Exception as e:
            print(f"❌ [DEBUG] 이미지 디코딩 실패: {e}")
            raise HTTPException(status_code=400, detail=f"이미지 디코딩 실패: {str(e)}")

        # 2. DB에 분석 요청 저장
        try:
            temp_image_url = f"temp_single_{int(time.time())}.jpg"
            db_request = AnalysisRequestCRUD.create(
                db=db,
                user_id=TEMP_USER_ID,
                image_url=temp_image_url,
                analysis_type=AnalysisType.SINGLE
            )
            print(f"✅ [DEBUG] DB 요청 저장 완료 - ID: {db_request.id}")
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

        # 6. 결과가 성공적인지 확인
        if not result["disease_status"].startswith(("분석 실패", "이미지 유효성")):
            try:
                # 성공: 결과 저장 (단일 분석이므로 detection_data 구조 다름)
                single_detection_data = [{
                    "crop_type": result["crop_type"],
                    "disease_status": result["disease_status"],
                    "confidence": result.get("confidence", 0.0),
                    "analysis_type": "single"
                }]
                
                db_result = AnalysisResultCRUD.create(
                    db=db,
                    request_id=db_request.id,
                    total_detections=1,  # 단일 분석은 항상 1개
                    result_image_url=f"single_result_{db_request.id}.jpg",
                    detection_data=single_detection_data,
                    processing_status="성공"
                )
                
                AnalysisRequestCRUD.update_status(
                    db, db_request.id, RequestStatus.COMPLETED, processing_time_ms
                )
                
                print(f"✅ [DEBUG] 단일 분석 결과 저장 완료")
                
            except Exception as e:
                print(f"❌ [DEBUG] 결과 저장 실패: {e}")
                AnalysisRequestCRUD.update_status(db, db_request.id, RequestStatus.FAILED)
        else:
            # 실패
            AnalysisRequestCRUD.update_status(
                db, db_request.id, RequestStatus.FAILED, processing_time_ms
            )
            print(f"❌ [DEBUG] 분석 결과 오류: {result['disease_status']}")
            raise HTTPException(status_code=500, detail=result["disease_status"])

        print("✅ [DEBUG] analyze_single 완료")
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