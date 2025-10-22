# plugins/antonym_plugin.py
import json
import os

ANTONYM_FILE = "plugins/antonyms.json"

class AntonymHandler:
    def __init__(self):
        # Nếu chưa có file antonyms.json thì tạo mới
        if not os.path.exists(ANTONYM_FILE):
            with open(ANTONYM_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)

        # Load dữ liệu antonym
        with open(ANTONYM_FILE, "r", encoding="utf-8") as f:
            self.patterns = json.load(f)

    def save_patterns(self):
        with open(ANTONYM_FILE, "w", encoding="utf-8") as f:
            json.dump(self.patterns, f, ensure_ascii=False, indent=2)

    def can_handle(self, command: str) -> bool:
        """Xử lý mọi input vì có thể học từ mới"""
        return True  

    def handle(self, command: str) -> str:
        # Nếu đã biết
        if command in self.patterns:
            return f"🔄 Ngược lại của '{command}' là: '{self.patterns[command]}'"

        # Nếu là antonym của cái khác
        for k, v in self.patterns.items():
            if v == command:
                return f"🔄 Ngược lại của '{command}' là: '{k}'"

        # Nếu chưa biết → hỏi lại
        antonym = input(f"❓ Tôi chưa biết ngược lại của '{command}'. Bạn hãy nhập: ")
        if antonym.strip():
            self.patterns[command] = antonym.strip()
            # Đồng thời lưu ngược lại
            self.patterns[antonym.strip()] = command
            self.save_patterns()
            return f"✅ Đã học: '{command}' ↔ '{antonym.strip()}'"
        return "🤷 Không nhận được câu trả lời."


# Đăng ký plugin
def register(assistant):
    assistant.handlers.append(AntonymHandler())


plugin_info = {
    "enabled": True,
    "register": register,
    "command_handle": ["antonym", "ngược nghĩa", "đảo ngược"]
}