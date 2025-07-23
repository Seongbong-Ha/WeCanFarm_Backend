import numpy as np
from PIL import Image
from tensorflow.keras.applications.resnet50 import preprocess_input
from .model_manager import model_manager

def run_resnet_inference(image: Image.Image, crop_type: str = 'pepper') -> dict:
    """
    작물별 질병 분류
    Args:
        image: 분류할 이미지
        crop_type: 작물 타입 ('pepper', 'tomato', 등) - 기본값 'pepper'로 기존 호환성 유지
    """
    if not model_manager.is_crop_supported(crop_type):
        return {
            "crop_type": crop_type,
            "disease_status": f"{crop_type} 모델이 지원되지 않습니다."
        }
    
    try:
        # 이미지 전처리
        processed_image = _preprocess_image(image)
        
        # 모델 추론
        model = model_manager.get_model(crop_type)
        predictions = model.predict(processed_image, verbose=0)
        predicted_idx = np.argmax(predictions[0])
        
        # 결과 해석
        class_labels = model_manager.get_class_labels(crop_type)
        korean_labels = model_manager.get_korean_labels(crop_type)
        
        class_name = class_labels.get(predicted_idx, "알 수 없음")
        disease_status = korean_labels.get(class_name, "알 수 없음")
        confidence = float(np.max(predictions[0]))
        
        return {
            "crop_type": crop_type,
            "disease_status": disease_status,
            "confidence": confidence,
            "predicted_class": class_name
        }
        
    except Exception as e:
        print(f"❌ {crop_type} 추론 중 오류: {e}")
        return {
            "crop_type": crop_type,
            "disease_status": f"추론 실패: {str(e)}"
        }

def _preprocess_image(image: Image.Image) -> np.ndarray:
    """이미지 전처리"""
    image = image.convert("RGB").resize((224, 224))
    image_array = np.array(image)
    image_array = preprocess_input(image_array)
    return np.expand_dims(image_array, axis=0)