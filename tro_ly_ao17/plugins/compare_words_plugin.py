# sử dụng 
# so sánh từ trong file1.txt và file2.txt
# plugins/compare_words_plugin.py

import re
import os
from __main__  import ICommandHandler

# Hàm xử lý chính
def compare_words(file1: str, file2: str) -> dict:
    def read_words(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
            return set(re.findall(r'\b\w+\b', content))  # Tách từ bằng regex

    words1 = read_words(file1)
    words2 = read_words(file2)

    missing_in_file2 = words1 - words2
    missing_in_file1 = words2 - words1

    return {
        f"Thiếu trong {os.path.basename(file2)}": sorted(missing_in_file2),
        f"Thiếu trong {os.path.basename(file1)}": sorted(missing_in_file1)
    }

# Lớp Command Handler để người dùng nhập lệnh tự nhiên
class CompareWordsCommand(ICommandHandler):
    def can_handle(self, command: str) -> bool:
        return command.startswith("so sánh từ trong ")

    def handle(self, command: str) -> bool:
        try:
            parts = command[len("so sánh từ trong "):].strip().split(" và ")
            if len(parts) != 2:
                print("❌ Cú pháp sai. Dùng: so sánh từ trong <file1.txt> và <file2.txt>")
                return True

            file1, file2 = parts[0].strip(), parts[1].strip()

            if not os.path.exists(file1) or not os.path.exists(file2):
                print("❌ Một trong hai file không tồn tại.")
                return True

            result = compare_words(file1, file2)

            print("\n📊 Kết quả so sánh từ:\n")
            for label, words in result.items():
                print(f"- {label} ({len(words)} từ):")
                if words:
                    print(", ".join(words))
                else:
                    print("Không có từ nào thiếu.")
                print()
            return True

        except Exception as e:
            print(f"⚠️ Lỗi khi xử lý: {e}")
            return True

# Plugin metadata để hệ thống trợ lý ảo nhận dạng và đăng ký
plugin_info = {
    "enabled": True,
    "methods": [
        {
            "class_name": "CompareWords",
            "method_name": "compare_txt_files",
            "version": "1.0",
            "function": compare_words,
            "description": "So sánh từ giữa 2 file txt để tìm từ bị thiếu"
        }
    ],
    "classes": [],
    "description" : "so sánh từ còn thiếu của nhau trong file1.txt và file2.txt",
    "register": lambda assistant: assistant.handlers.insert(2, CompareWordsCommand())
}