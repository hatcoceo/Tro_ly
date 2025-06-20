from abc import ABC, abstractmethod
import numpy as np
from typing import List
from sklearn.linear_model import LogisticRegression
import pickle
import os
import ast

class ICommandHandler(ABC):
    @abstractmethod
    def can_handle(self, command: str) -> bool:
        pass

    @abstractmethod
    def handle(self, command: str) -> bool:
        pass

class AITrainer:
    def __init__(self):
        self.model = None
        self.model_path = "ai_model.pkl"

    def train(self, X: List[List[float]], y: List[int], model_type: str = "logistic") -> str:
        """Huấn luyện mô hình AI với dữ liệu đầu vào."""
        try:
            if model_type == "logistic":
                self.model = LogisticRegression()
                self.model.fit(X, y)
                with open(self.model_path, "wb") as f:
                    pickle.dump(self.model, f)
                return "✅ Mô hình đã được huấn luyện và lưu thành công!"
        except Exception as e:
            return f"⚠️ Lỗi khi huấn luyện mô hình: {str(e)}"

    def predict(self, X: List[List[float]]) -> List[int]:
        """Dự đoán với mô hình đã huấn luyện."""
        try:
            if self.model is None and os.path.exists(self.model_path):
                with open(self.model_path, "rb") as f:
                    self.model = pickle.load(f)
            if self.model is None:
                return ["⚠️ Mô hình chưa được huấn luyện!"]
            predictions = self.model.predict(X)
            return predictions.tolist()
        except Exception as e:
            return [f"⚠️ Lỗi khi dự đoán: {str(e)}"]

class AITrainerCommandHandler(ICommandHandler):
    def __init__(self, ai_trainer: AITrainer):
        self.ai_trainer = ai_trainer

    def can_handle(self, command: str) -> bool:
        """Kiểm tra xem lệnh có liên quan đến AI không."""
        return command.startswith("ai_train") or command.startswith("ai_predict")

    def handle(self, command: str) -> bool:
        """Xử lý các lệnh liên quan đến huấn luyện và dự đoán AI."""
        try:
            if command.startswith("ai_train"):
                parts = command.split(" ", 1)
                if len(parts) < 2:
                    print("⚠️ Vui lòng cung cấp dữ liệu huấn luyện! (Ví dụ: ai_train [[1,2], [3,4], [5,6]], [0,1,0])")
                    return True
                try:
                    data_str = parts[1].strip()
                    if not (data_str.startswith("[") and "," in data_str):
                        raise ValueError("Dữ liệu phải có định dạng: [[...], [...]], [...]")
                    X, y = ast.literal_eval(data_str)
                    result = self.ai_trainer.train(X, y)
                    print(result)
                except (ValueError, SyntaxError) as e:
                    print(f"⚠️ Lỗi cú pháp dữ liệu: {str(e)}. Vui lòng nhập theo định dạng: [[x1,x2], [x3,x4]], [y1,y2]")
                return True

            elif command.startswith("ai_predict"):
                parts = command.split(" ", 1)
                if len(parts) < 2:
                    print("⚠️ Vui lòng cung cấp dữ liệu dự đoán! (Ví dụ: ai_predict [[1,2], [3,4]])")
                    return True
                try:
                    X = ast.literal_eval(parts[1].strip())
                    predictions = self.ai_trainer.predict(X)
                    print(f"📊 Kết quả dự đoán: {predictions}")
                except (ValueError, SyntaxError) as e:
                    print(f"⚠️ Lỗi cú pháp dữ liệu: {str(e)}. Vui lòng nhập theo định dạng: [[x1,x2], [x3,x4]]")
                return True

        except Exception as e:
            print(f"⚠️ Lỗi khi xử lý lệnh: {str(e)}")
            return False
        return True

def register(core):
    """Đăng ký plugin với VirtualAssistantCore."""
    ai_trainer = AITrainer()
    handler = AITrainerCommandHandler(ai_trainer)
    core.handlers.append(handler)
    print("✅ Đã đăng ký AITrainerCommandHandler")

    core.version_manager.register_method_version(
        class_name="AITrainer",
        method_name="train",
        version="v1",
        method_ref=ai_trainer.train,
        description="Huấn luyện mô hình Logistic Regression",
        mode="replace"
    )

    core.version_manager.register_method_version(
        class_name="AITrainer",
        method_name="predict",
        version="v1",
        method_ref=ai_trainer.predict,
        description="Dự đoán với mô hình Logistic Regression",
        mode="replace"
    )

    core.version_manager.register_class_version(
        class_name="AITrainer",
        version="v1",
        class_ref=AITrainer
    )

plugin_info = {
    "enabled": True,
    "register": register,
    "methods": [
        {
            "class_name": "AITrainer",
            "method_name": "train",
            "version": "v1",
            "function": AITrainer.train,
            "description": "Huấn luyện mô hình Logistic Regression",
            "mode": "replace"
        },
        {
            "class_name": "AITrainer",
            "method_name": "predict",
            "version": "v1",
            "function": AITrainer.predict,
            "description": "Dự đoán với mô hình Logistic Regression",
            "mode": "replace"
        }
    ],
    "classes": [
        {
            "class_name": "AITrainer",
            "version": "v1",
            "class_ref": AITrainer
        }
    ]
          }
