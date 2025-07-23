import os
import tensorflow as tf
from typing import Dict, Optional

class ModelManager:
    def __init__(self):
        self.models: Dict[str, tf.keras.Model] = {}
        self.class_labels: Dict[str, Dict[int, str]] = {}
        self.korean_labels: Dict[str, Dict[str, str]] = {}
        self._load_all_models()
    
    def _load_all_models(self):
        """모든 작물 모델을 로드"""
        self._load_pepper_model()
        # 추후 확장: self._load_tomato_model(), self._load_cucumber_model() 등
    
    def _load_pepper_model(self):
        """고추 모델 로드"""
        model_path = 'WeCanFarm_Server/app/models/pepper_disease_model.keras'
        try:
            self.models['pepper'] = tf.keras.models.load_model(model_path, compile=False)
            print("✅ 고추 모델 로딩 성공")
            
            # 고추 모델 클래스 정보
            self.class_labels['pepper'] = {
                0: "BacterialSpot_4",
                1: "PMMoV_3", 
                2: "normal_0"
            }
            
            self.korean_labels['pepper'] = {
                "BacterialSpot_4": "고추점무늬병",
                "PMMoV_3": "고추마일드모틀바이러스",
                "normal_0": "정상"
            }
            
        except Exception as e:
            print(f"❌ 고추 모델 로딩 실패: {e}")
            self.models['pepper'] = None
    
    def _load_tomato_model(self):
        """토마토 모델 로드 (추후 구현)"""
        pass
    
    def get_model(self, crop_type: str) -> Optional[tf.keras.Model]:
        """작물별 모델 반환"""
        return self.models.get(crop_type)
    
    def get_class_labels(self, crop_type: str) -> Optional[Dict[int, str]]:
        """작물별 클래스 라벨 반환"""
        return self.class_labels.get(crop_type)
    
    def get_korean_labels(self, crop_type: str) -> Optional[Dict[str, str]]:
        """작물별 한국어 라벨 반환"""
        return self.korean_labels.get(crop_type)
    
    def get_available_crops(self) -> list:
        """사용 가능한 작물 목록 반환"""
        return [crop for crop, model in self.models.items() if model is not None]
    
    def is_crop_supported(self, crop_type: str) -> bool:
        """작물이 지원되는지 확인"""
        return crop_type in self.models and self.models[crop_type] is not None

# 전역 ModelManager 인스턴스
model_manager = ModelManager()