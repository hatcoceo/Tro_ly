import json
import os
from datetime import datetime
from typing import Any

# đường dẫn file lưu dữ liệu
DATA_FILE = "run_stats.json"

# Tên class handler để load vào core
class RunCounterHandler:
    def __init__(self, assistant: Any):
        self.assistant = assistant
        self.load_data()
        self.increment_run_count()
        self.save_data()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = {
                "run_count": 0,
                "run_history": []
            }

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def increment_run_count(self):
        self.data["run_count"] += 1
        current_time = datetime.now().isoformat()
        self.data["run_history"].append(current_time)

    def can_handle(self, command: str) -> bool:
        # Ví dụ nhận lệnh:
        return command.lower().strip() in [
            "thông tin chạy",
            "thong tin chay",
            "run info",
            "run count"
        ]

    def handle(self, command: str) -> bool:
        count = self.data["run_count"]
        run_history = self.data["run_history"]
        
        print(f"🚀 Tổng số lần chạy: {count}")
        print("📜 Lịch sử chạy:")
        
        if not run_history:
            print("Chưa có lần chạy nào được ghi lại.")
        else:
            for i, run_time in enumerate(run_history, 1):
                dt = datetime.fromisoformat(run_time)
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                print(f"{i}. {formatted_time}")
        
        return True


# Plugin Info để Loader tự động nạp
plugin_info = {
    "enabled": True,
    "register": lambda assistant: assistant.handlers.insert(2, RunCounterHandler(assistant)),
    "methods": [],
    "classes": []
}