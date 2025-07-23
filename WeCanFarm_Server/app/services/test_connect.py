# services/test_connection.py (테스트용)
from WeCanFarm_Server.app.services.model_manager import model_manager
from WeCanFarm_Server.app.services.inference import run_resnet_inference

print("✅ Import 성공!")
print("지원 작물:", model_manager.get_available_crops())