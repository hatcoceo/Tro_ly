# plugins/plugin_b.py

class AddCommandHandler:
    def __init__(self, assistant):
        self.assistant = assistant

    def can_handle(self, command: str) -> bool:
        return command.lower().startswith("cộng")

    def handle(self, command: str) -> bool:
        try:
            # Câu lệnh: "cộng 3 và 5"
            parts = command.lower().replace("cộng", "").strip().split("và")
            a = int(parts[0].strip())
            b = int(parts[1].strip())

            result = self.assistant.call_method("MathPluginA", "add", a, b, version="1.0")
            print(f"✅ Kết quả: {result}")
        except Exception as e:
            print(f"⚠️ Lỗi xử lý: {e}")
        return True

plugin_info = {
    "enabled": True,
    "register": lambda assistant: assistant.handlers.insert (2, AddCommandHandler(assistant)),
    "methods": [],
    "classes": []
}