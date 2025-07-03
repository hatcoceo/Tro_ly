import os
from typing import List

FILE_PATH = "tri_thuc.txt"

# ======= LỚP XỬ LÝ CRUD =======

class KnowledgeManager:
    def add(self, data: str) -> str:
        with open(FILE_PATH, "a", encoding="utf-8") as f:
            f.write(data.strip() + "\n")
        return "✅ Đã thêm dòng kiến thức."

    def read(self) -> str:
        if not os.path.exists(FILE_PATH):
            return "📄 File chưa có dữ liệu."
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if not lines:
            return "📭 Không có dữ liệu."
        return "".join(f"{i+1}. {line}" for i, line in enumerate(lines))

    def update(self, line_number: int, new_data: str) -> str:
        if not os.path.exists(FILE_PATH):
            return "📄 File chưa có dữ liệu."
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if line_number < 1 or line_number > len(lines):
            return "❌ Số dòng không hợp lệ."
        lines[line_number - 1] = new_data.strip() + "\n"
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return f"✅ Đã cập nhật dòng {line_number}."

    def delete(self, line_number: int) -> str:
        if not os.path.exists(FILE_PATH):
            return "📄 File chưa có dữ liệu."
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if line_number < 1 or line_number > len(lines):
            return "❌ Số dòng không hợp lệ."
        removed = lines.pop(line_number - 1)
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return f"🗑️ Đã xóa dòng {line_number}: {removed.strip()}"

# ======= HANDLER CHO LỆNH NGƯỜI DÙNG =======

class CRUDCommandHandler:
    def __init__(self, core):
        self.core = core

    def can_handle(self, command: str) -> bool:
        return any(
            command.lower().startswith(prefix)
            for prefix in ["thêm:", "xem", "sửa:", "xóa:"]
        )

    def handle(self, command: str) -> bool:
        cmd = command.strip()

        if cmd.startswith("thêm:"):
            data = cmd[5:].strip()
            result = self.core.call_class_method("KnowledgeManager", "add", data, version="v1")
        elif cmd == "xem":
            result = self.core.call_class_method("KnowledgeManager", "read", version="v1")
        elif cmd.startswith("sửa:"):
            try:
                rest = cmd[4:].strip()
                line_number, new_text = rest.split(":", 1)
                result = self.core.call_class_method(
                    "KnowledgeManager", "update", int(line_number.strip()), new_text.strip(), version="v1"
                )
            except Exception:
                result = "❌ Cú pháp sửa không đúng. Dạng: sửa: <số dòng>: <nội dung mới>"
        elif cmd.startswith("xóa:"):
            try:
                line_number = int(cmd[4:].strip())
                result = self.core.call_class_method("KnowledgeManager", "delete", line_number, version="v1")
            except:
                result = "❌ Cú pháp xóa không đúng. Dạng: xóa: <số dòng>"
        else:
            result = "🤷‍♂️ Không hiểu yêu cầu CRUD."

        print(result)
        return True

# ======= THÔNG TIN PLUGIN =======

def register(core):
    handler = CRUDCommandHandler(core)
    core.handlers.append(handler)

plugin_info = {
   "enabled": True,
    "register": register,
    "classes": [
        {
            "class_name": "KnowledgeManager",
            "version": "v1",
            "class_ref": KnowledgeManager,
        }
    ]
}