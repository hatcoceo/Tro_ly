from typing import List
from __main__ import ICommandHandler

# Mô tả plugin
plugin_info = {
    "enabled": True,
    "register": lambda assistant: assistant.handlers.insert(1, NegativeChainHandler()),
    "methods": [],
    "classes": []
}

# Bộ luật tiêu cực theo chuỗi nhân quả
NEGATIVE_CHAIN_RULES = {
    "con đau bệnh": ["tốn tiền ", "tốn thời gian ", "tốn sức khỏe ", "tốn cảm xúc"],
    "ngồi chơi 5 ngày": ["chán", "tinh thần bất an", "xóa sạch sẽ"],
    "ngủ muộn": ["mệt mỏi", "khó tập trung", "giảm hiệu suất"],
}

class NegativeChainHandler(ICommandHandler):
    def can_handle(self, command: str) -> bool:
        return command.lower().startswith("nếu") and any(neg in command for neg in NEGATIVE_CHAIN_RULES)

    def handle(self, command: str) -> bool:
        found_neg = None
        for cause in NEGATIVE_CHAIN_RULES:
            if cause in command:
                found_neg = cause
                break

        if not found_neg:
            print("🤷 Không nhận diện được điều tiêu cực trong câu.")
            return True

        consequences = NEGATIVE_CHAIN_RULES[found_neg]
        print(f"❗ Nếu '{found_neg}', thì hậu quả sẽ là:")
        for effect in consequences:
            print(f"  👉 {effect}")

        print(f"\n✅ Nhưng nếu bạn **tránh được '{found_neg}'**, thì có thể tránh được các hậu quả trên.")
        return True