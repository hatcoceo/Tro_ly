# plugins/plugin_greeting.py
from. import demo_import_plugin_a   # import plugin cùng thư mục

def can_handle(command: str) -> bool:
    return command.lower() in ["chào", "hi", "hello", "xin chào"]

def handle(command: str) -> str:
    hour = demo_import_plugin_a.get_current_hour()
    if hour < 12:
        print( "☀️ Chào buổi sáng! Bạn cần giúp gì?")
    elif hour < 18:
        print( "🌤️ Chào buổi chiều! Tôi có thể giúp gì?")
    else:
        print( "🌙 Chào buổi tối! Bạn cần hỗ trợ gì không?")

class GreetingHandler:
    @staticmethod
    def can_handle(cmd):
        return can_handle(cmd)
    @staticmethod
    def handle(cmd):
        return handle(cmd)

plugin_info = {
    "enabled": True,
    "register": lambda assistant: assistant.handlers.append(GreetingHandler())
}