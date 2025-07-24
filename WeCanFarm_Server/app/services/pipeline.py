# app/services/pipeline.py
from PIL import Image
from typing import List, Dict
from ..utils.image_handler import (
    yolo_detection,
    image_to_base64,
    validate_image,
    prepare_image_for_model
)
from .inference import run_resnet_inference

def process_image_pipeline(image: Image.Image) -> dict:
    """
    전체 이미지 처리 파이프라인 (바운딩박스 표시 없이)
    Args:
        image: 입력 이미지
    Returns:
        {
            "image_base64": "원본 이미지",
            "detections": [감지 결과 리스트],
            "total_detections": 총 감지 개수,
            "processing_status": "성공/실패"
        }
    """
    try:
        # 1. 이미지 유효성 검사
        if not validate_image(image):
            return {
                "image_base64": "",
                "detections": [],
                "total_detections": 0,
                "processing_status": "이미지 유효성 검사 실패"
            }
        
        # 2. YOLO 객체 감지
        yolo_detections = yolo_detection(image)
        
        # 3. 각 감지된 객체별로 질병 분류 (전체 이미지 사용)
        final_detections = []
        
        if len(yolo_detections) > 0:
            # 전체 이미지로 한 번만 ResNet 추론 (효율성)
            print("🔍 전체 이미지로 질병 분류 실행")
            disease_result = run_resnet_inference(image, 'pepper')
            
            for detection in yolo_detections:
                bbox = detection["bbox"]
                crop_type = detection["crop_type"]
                yolo_confidence = detection["confidence"]
                
                # 모든 감지된 객체에 동일한 질병 분류 결과 적용
                final_detection = {
                    "bbox": bbox,
                    "crop_type": crop_type,
                    "disease_status": disease_result.get("disease_status", "알 수 없음"),
                    "disease_confidence": disease_result.get("confidence", 0.0),
                    "yolo_confidence": yolo_confidence,
                    "label": f"{crop_type}: {disease_result.get('disease_status', '알 수 없음')}"
                }
                
                final_detections.append(final_detection)
                print(f"🔍 감지 객체 #{len(final_detections)}: {detection['crop_type']} - {disease_result.get('disease_status', '알 수 없음')}")
        
        # 4. 원본 이미지를 그대로 사용 (바운딩박스 그리기 제거)
        result_image = image
        print(f"✅ 원본 이미지 사용: {len(final_detections)}개 객체 감지됨")
        
        # 5. 결과 이미지를 base64로 인코딩
        result_base64 = image_to_base64(result_image)
        
        return {
            "image_base64": result_base64,
            "detections": final_detections,
            "total_detections": len(final_detections),
            "processing_status": "성공"
        }
        
    except Exception as e:
        print(f"❌ 파이프라인 처리 중 오류: {e}")
        return {
            "image_base64": "",
            "detections": [],
            "total_detections": 0,
            "processing_status": f"처리 실패: {str(e)}"
        }

def process_single_crop_analysis(image: Image.Image, crop_type: str = 'pepper') -> dict:
    """
    단일 작물 분석 (기존 방식 호환용) - 전체 이미지로 분석
    Args:
        image: 입력 이미지
        crop_type: 작물 타입
    Returns:
        단일 분석 결과
    """
    try:
        if not validate_image(image):
            return {
                "crop_type": crop_type,
                "disease_status": "이미지 유효성 검사 실패"
            }
        
        # ResNet으로 전체 이미지 직접 분석 (YOLO 없이)
        print(f"🔍 단일 분석: 전체 이미지로 {crop_type} 질병 분류")
        result = run_resnet_inference(image, crop_type)
        
        print(f"✅ 단일 분석 완료: {result.get('disease_status', '알 수 없음')}")
        return result
        
    except Exception as e:
        print(f"❌ 단일 작물 분석 중 오류: {e}")
        return {
            "crop_type": crop_type,
            "disease_status": f"분석 실패: {str(e)}"
        }