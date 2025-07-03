from __main__  import ICommandHandler

def calculate(expression: str) -> float:
    try:
        result = eval(expression, {"__builtins__": {}})
        return result
    except Exception as e:
        print(f"⚠️ Lỗi tính toán: {e}")
        return None

class CalculatorHandler(ICommandHandler):
    def __init__(self, assistant):
        self.assistant = assistant

    def can_handle(self, command: str) -> bool:
        return command.lower().startswith("tính ")

    def handle(self, command: str) -> bool:
        expr = command[5:].strip()
        result = self.assistant.call_method("Calculator", "calculate", expr, version="v1")
        if result is not None:
            print(f"🧮 Kết quả: {result}")
        else:
            print("❌ Không tính được biểu thức.")
        return True

def register(assistant):
    assistant.handlers.append(CalculatorHandler(assistant))
    print("✅ CalculatorHandler đã được đăng ký từ plugin.")

plugin_info = {
    "enabled": True,
    "methods": [
        {
            "class_name": "Calculator",
            "method_name": "calculate",
            "version": "v1",
            "function": calculate,
            "description": "Tính toán biểu thức",
            "mode": "replace"
        }
    ],
    "register": register
}