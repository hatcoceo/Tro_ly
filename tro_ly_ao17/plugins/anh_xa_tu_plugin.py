# plugin_antonym_mapper.py

from typing import List
from abc import ABC
#from interfaces import ICommandHandler

class AntonymMapperHandler():
    def __init__(self):
        # Danh sách ánh xạ từ ngữ đối lập
        self.antonym_map = {
            "xa": "gần", "gần": "xa",
            "trước": "sau", "sau": "trước",
            "trên": "dưới", "dưới": "trên",
            "trái": "phải", "phải": "trái",
            "nóng": "lạnh", "lạnh": "nóng",
            "cao": "thấp", "thấp": "cao",
            "nhanh": "chậm", "chậm": "nhanh",
            "sáng": "tối", "tối": "sáng",
            "vào": "ra", "ra": "vào",
            "mạnh": "yếu", "yếu": "mạnh"
        }

    def can_handle(self, command: str) -> bool:
        return command.lower().startswith("đối lập của ")

    def handle(self, command: str) -> bool:
        parts = command.lower().split("đối lập của ", 1)
        if len(parts) < 2:
            print("❌ Bạn cần nhập dạng: đối lập của [từ]")
            return True

        word = parts[1].strip()
        antonym = self.antonym_map.get(word)

        if antonym:
            print(f"🔁 Từ đối lập với '{word}' là: '{antonym}'")
        else:
            print(f"🤔 Không tìm thấy từ đối lập với '{word}' trong danh sách.")
        return True

# Thông tin plugin
plugin_info = {
    "enabled": True,
    "register": lambda assistant: assistant.handlers.insert(1, AntonymMapperHandler()),
    "methods": [],
    "classes": []
}