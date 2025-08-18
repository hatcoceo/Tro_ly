import os
import sys
from typing import Any

class RestartHandler:
    def can_handle(self, command: str) -> bool:
        return command in ["restart", "khởi động lại"]

    def handle(self, command: str) -> None:
        print("🔄 Đang khởi động lại trợ lý ảo...")
        python = sys.executable
        os.execl(python, python, *sys.argv)

def register(assistant: Any) -> None:
    handler = RestartHandler()
    assistant.handlers.append(handler)

plugin_info = {
    "enabled": True,
    "register": register,
    "command_handle": ["restart", "khởi động lại"]
}