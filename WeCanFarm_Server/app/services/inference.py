import os
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras.applications.resnet50 import preprocess_input

# ✅ 모델 경로 설정 (.keras or .h5)
MODEL_PATH = 'WeCanFarm_Server/app/models/pepper_disease_model.keras'

# ✅ 모델 로딩
try:
    model = tf.keras.models.load_model(MODEL_PATH, compile=False)
    print("✅ 모델 로딩 성공")
except Exception as e:
    print("❌ 모델 로딩 실패:", e)
    model = None

# ✅ 클래스 정보
CLASS_LABELS = {
    0: "BacterialSpot_4",       # 고추점무늬병
    1: "PMMoV_3",               # 고추마일드모틀바이러스
    2: "normal_0"               # 정상
}

KOREAN_LABELS = {
    "BacterialSpot_4": "고추점무늬병",
    "PMMoV_3": "고추마일드모틀바이러스",
    "normal_0": "정상"
}

# ✅ 추론 함수
def run_resnet_inference(image: Image.Image) -> dict:
    if model is None:
        return {
            "crop_type": "고추",
            "disease_status": "모델 로딩 실패"
        }

    try:
        # 이미지 전처리
        image = image.convert("RGB").resize((224, 224))
        image_array = np.array(image)
        image_array = preprocess_input(image_array)
        image_batch = np.expand_dims(image_array, axis=0)

        # 모델 추론
        predictions = model.predict(image_batch, verbose=0)
        predicted_idx = np.argmax(predictions[0])
        class_name = CLASS_LABELS.get(predicted_idx, "알 수 없음")
        disease_status = KOREAN_LABELS.get(class_name, "알 수 없음")

        return {
            "crop_type": "고추",
            "disease_status": disease_status
        }
    except Exception as e:
        print("❌ 추론 중 오류:", e)
        return {
            "crop_type": "고추",
            "disease_status": f"추론 실패: {str(e)}"
        }
