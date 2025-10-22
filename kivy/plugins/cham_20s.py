# plugins3/slow_plugin.py
import time

class SlowPlugin:
    def can_handle(self, command: str) -> bool:
        return command == "chậm 20s"

    def handle(self, command: str) -> str:
        # Giả lập xử lý chậm 20 giây
        time.sleep(20)
        return "⏱️ Xong rồi, tôi đã chờ 20 giây!"

def register(assistant):
    assistant.handlers.append(SlowPlugin())

plugin_info = {
    "enabled": True,
    "register": register,
    "command_handle": ["chậm 20s"]
}