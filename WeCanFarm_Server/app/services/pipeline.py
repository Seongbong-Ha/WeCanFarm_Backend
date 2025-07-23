# services/pipeline.py
from PIL import Image
from typing import List, Dict
from ..utils.image_handler import (
    mock_yolo_detection, 
    crop_image, 
    draw_bounding_boxes, 
    image_to_base64,
    validate_image,
    prepare_image_for_model
)
from .inference import run_resnet_inference

def process_image_pipeline(image: Image.Image) -> dict:
    """
    전체 이미지 처리 파이프라인
    Args:
        image: 입력 이미지
    Returns:
        {
            "image_base64": "바운딩박스가 그려진 최종 이미지",
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
        
        # 2. YOLO 객체 감지 (현재는 Mock)
        yolo_detections = mock_yolo_detection(image)
        
        # 3. 각 감지된 객체별로 질병 분류
        final_detections = []
        
        for detection in yolo_detections:
            bbox = detection["bbox"]
            crop_type = detection["crop_type"]
            yolo_confidence = detection["confidence"]
            
            # 3.1. 바운딩박스로 이미지 크롭
            cropped_image = crop_image(image, bbox)
            
            # 3.2. 크롭된 이미지가 너무 작으면 스킵
            if cropped_image.size[0] < 32 or cropped_image.size[1] < 32:
                continue
            
            # 3.3. ResNet으로 질병 분류
            disease_result = run_resnet_inference(cropped_image, crop_type)
            
            # 3.4. 결과 통합
            final_detection = {
                "bbox": bbox,
                "crop_type": crop_type,
                "disease_status": disease_result.get("disease_status", "알 수 없음"),
                "disease_confidence": disease_result.get("confidence", 0.0),
                "yolo_confidence": yolo_confidence,
                "label": f"{crop_type}: {disease_result.get('disease_status', '알 수 없음')}"
            }
            
            final_detections.append(final_detection)
        
        # 4. 원본 이미지에 바운딩박스 + 라벨 그리기
        result_image = draw_bounding_boxes(image, final_detections)
        
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
    단일 작물 분석 (기존 방식 호환용)
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
        
        # ResNet으로 직접 분석 (YOLO 없이)
        result = run_resnet_inference(image, crop_type)
        return result
        
    except Exception as e:
        print(f"❌ 단일 작물 분석 중 오류: {e}")
        return {
            "crop_type": crop_type,
            "disease_status": f"분석 실패: {str(e)}"
        }
