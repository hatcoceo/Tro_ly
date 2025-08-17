import webbrowser
from typing import Any

class OpenWebHandler:
    def __init__(self, url: str = "https://www.google.com"):
        self.url = url

    def can_handle(self, command: str) -> bool:
        return command.startswith("mở web") or command.startswith("open web")

    def handle(self, command: str) -> str:
        # Nếu lệnh có kèm URL thì dùng URL đó
        parts = command.split(maxsplit=2)
        if len(parts) == 3:
            self.url = parts[2]
        webbrowser.open(self.url)
        return f"🌐 Đang mở trang web: {self.url}"

# Thông tin plugin
plugin_info = {
    "enabled": True,
    "register": lambda assistant: assistant.handlers.append(OpenWebHandler()),
    "command_handle": ["mở web", "open web"]
}
