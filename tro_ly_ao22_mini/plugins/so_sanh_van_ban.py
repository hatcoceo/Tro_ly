import difflib
from typing import Any

class DiffHandler:
    def can_handle(self, command: str) -> bool:
        return command.startswith("diff ")

    def handle(self, command: str):
        try:
            parts = command.split()
            if len(parts) < 3:
                print("❌ Cú pháp: diff <file1> <file2>")
                return

            file1, file2 = parts[1], parts[2]

            with open(file1, "r", encoding="utf-8") as f1:
                text1 = f1.readlines()

            with open(file2, "r", encoding="utf-8") as f2:
                text2 = f2.readlines()

            print(f"\n🔍 So sánh: {file1} ↔ {file2}\n")

            diff = difflib.unified_diff(
                text1, text2,
                fromfile=file1,
                tofile=file2,
                lineterm=""
            )

            has_diff = False
            lines = []
            for line in diff:
                has_diff = True
                lines.append(line)
                #print(line)

            if not has_diff:
                result = "✅ Hai file giống nhau hoàn toàn"
            else:
                result = "\n".join(lines)
            print(result)   # hiển thị
            return result   # trả về cho plugin khác

        except FileNotFoundError:
            print("❌ Không tìm thấy file")
        except Exception as e:
            print(f"⚠️ Lỗi: {e}")


def register(assistant: Any):
    assistant.handlers.append(DiffHandler())


plugin_info = {
    "enabled": True,
    "register": register,
    "command_handle": ["diff van_ban_1.txt van_ban_2.txt"]
}