#sd: đếm file 
import os
from typing import Any

class CountFilesFoldersPlugin:
    def count(self, path: str = ".") -> str:
        if not os.path.exists(path):
            return f"❌ Đường dẫn không tồn tại: {path}"

        total_files = 0
        total_dirs = 0

        for root, dirs, files in os.walk(path):
            total_dirs += len(dirs)
            total_files += len(files)

        return f"📁 Thống kê tại '{os.path.abspath(path)}':\n- Thư mục: {total_dirs}\n- Tệp tin: {total_files}"

# Plugin info
plugin_info = {
    "enabled": True,
    "register": lambda assistant: assistant.handlers.insert (1, CountFilesFoldersHandler(assistant)),
    "methods": [
        {
            "class_name": "CountFilesFoldersPlugin",
            "method_name": "count",
            "version": "1.0",
            "function": CountFilesFoldersPlugin().count,
            "description": "Đếm số file và thư mục trong hệ thống",
        }
    ],
    "classes": [
        {
            "class_name": "CountFilesFoldersPlugin",
            "version": "1.0",
            "class_ref": CountFilesFoldersPlugin
        }
    ]
}

# Command handler
from __main__ import ICommandHandler

class CountFilesFoldersHandler(ICommandHandler):
    def __init__(self, assistant: Any):
        self.assistant = assistant

    def can_handle(self, command: str) -> bool:
        return command.startswith("đếm file") or command.startswith("đếm thư mục")

    def handle(self, command: str) -> bool:
        # Lấy đường dẫn nếu có, mặc định là "."
        parts = command.strip().split(" ", 2)
        path = parts[2] if len(parts) >= 3 else "."
        result = self.assistant.call_method("CountFilesFoldersPlugin", "count", path, version="1.0")
        print(result)
        return True