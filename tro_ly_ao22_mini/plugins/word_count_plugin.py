import os
import re

class WordCountHandler:
    def can_handle(self, command: str) -> bool:
        return command.startswith("count ")

    def handle(self, command: str) -> None:
        try:
            parts = command.split()

            if len(parts) < 2:
                print("⚠️ Thiếu đường dẫn file")
                return

            file_path = parts[1]
            no_number = "--no-number" in parts  # 👈 tùy chọn mới

            if not os.path.exists(file_path):
                print("❌ File không tồn tại!")
                return

            if not file_path.endswith(".txt"):
                print("⚠️ Chỉ hỗ trợ file .txt")
                return

            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

            if no_number:
                # 🔥 Chỉ lấy chữ (bỏ số)
                words = re.findall(r'\b[^\W\d_]+\b', text, flags=re.UNICODE)
                print("📄 Chế độ: KHÔNG tính số")
            else:
                # 🔥 Lấy cả chữ + số
                words = re.findall(r'\b\w+\b', text, flags=re.UNICODE)
                print("📄 Chế độ: Có tính số")

            word_count = len(words)

            print(f"👉 Số từ: {word_count}")

        except Exception as e:
            print(f"⚠️ Lỗi khi đọc file: {e}")


def register(assistant):
    assistant.handlers.append(WordCountHandler())


plugin_info = {
    "enabled": True,
    "register": register,
    "command_handle": [
        "count word.txt",
        "count word.txt --no-number"
    ]
}