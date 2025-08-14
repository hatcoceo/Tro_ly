plugin_info = {
    "enabled": True,
    "name": "8-Bit Register with Dependency (Extended)",
    "version": "1.1",
    "description": "Plugin mô phỏng thanh ghi 8-bit, hỗ trợ phụ thuộc, reset, lưu/tải cấu hình phụ thuộc.",
    "register": lambda assistant: assistant.handlers.insert(1, BitRegisterHandler(assistant)),
    "methods": [],
    "classes": []
}

from typing import Dict, List
import json, os
from __main__ import ICommandHandler

DEPENDENCY_FILE = "dependencies.json"

class BitRegister:
    def __init__(self):
        self.states: Dict[str, bool] = {f"B{i}": False for i in range(8)}
        self.dependencies: Dict[str, List[str]] = {}
        self.load_dependencies()

    def set_dependency(self, key: str, targets: List[str]) -> str:
        if key not in self.states:
            return f"⚠️ Bit không tồn tại: {key}"
        for t in targets:
            if t not in self.states:
                return f"⚠️ Bit không tồn tại: {t}"
        self.dependencies[key] = targets
        return f"✅ Thiết lập phụ thuộc: {key} => {', '.join(targets)}"

    def save_dependencies(self) -> str:
        with open(DEPENDENCY_FILE, "w") as f:
            json.dump(self.dependencies, f)
        return "✅ Đã lưu phụ thuộc ra file."

    def load_dependencies(self) -> str:
        if os.path.exists(DEPENDENCY_FILE):
            with open(DEPENDENCY_FILE, "r") as f:
                self.dependencies = json.load(f)
            return "✅ Đã tải phụ thuộc từ file."
        return "ℹ️ Không có file phụ thuộc để tải."

    def reset_register(self) -> str:
        for key in self.states:
            self.states[key] = False
        return "✅ Đã reset thanh ghi về 00000000"

    def set_bits_from_string(self, bitstring: str) -> str:
        if len(bitstring) != 8 or any(c not in "01" for c in bitstring):
            return "⚠️ Chuỗi phải có đúng 8 ký tự 0 hoặc 1"
        for i, bit in enumerate(reversed(bitstring)):
            self.states[f"B{i}"] = bit == "1"
        return f"✅ Đã thiết lập: {bitstring}"

    def toggle_bit(self, key: str, value: bool) -> List[str]:
        if key not in self.states:
            return [f"⚠️ Bit không tồn tại: {key}"]

        self.states[key] = value
        result = [f"🔁 {key} => {'1' if value else '0'}"]
        visited = set()

        def propagate(k):
            for dep in self.dependencies.get(k, []):
                if dep in visited:
                    continue
                visited.add(dep)
                self.states[dep] = value
                result.append(f"➡️ {dep} => {'1' if value else '0'}")
                propagate(dep)

        propagate(key)
        return result

    def view_register(self) -> str:
        bits = "".join(["1" if self.states[f"B{i}"] else "0" for i in reversed(range(8))])
        return f"🧮 Thanh ghi: {bits}"

class BitRegisterHandler(ICommandHandler):
    def __init__(self, assistant):
        self.assistant = assistant
        self.register = BitRegister()

    def can_handle(self, command: str) -> bool:
        return any(command.startswith(prefix) for prefix in [
            "bật bit", "tắt bit", "xem thanh ghi",
            "thiết lập ", "thiết lập phụ thuộc",
            "reset thanh ghi", "lưu phụ thuộc", "tải phụ thuộc"
        ])

    def handle(self, command: str) -> bool:
        cmd = command.strip().lower()

        if cmd.startswith("bật bit"):
            try:
                idx = int(cmd.replace("bật bit", "").strip())
                result = self.register.toggle_bit(f"B{idx}", True)
            except:
                result = ["⚠️ Cú pháp không hợp lệ."]

        elif cmd.startswith("tắt bit"):
            try:
                idx = int(cmd.replace("tắt bit", "").strip())
                result = self.register.toggle_bit(f"B{idx}", False)
            except:
                result = ["⚠️ Cú pháp không hợp lệ."]

        elif cmd == "xem thanh ghi":
            result = [self.register.view_register()]

        elif cmd.startswith("thiết lập phụ thuộc"):
            try:
                _, rest = cmd.split("thiết lập phụ thuộc")
                source, targets = rest.strip().upper().split("=>")
                source = source.strip()
                target_list = [t.strip() for t in targets.strip().split(",")]
                msg = self.register.set_dependency(source, target_list)
                result = [msg]
            except:
                result = ["⚠️ Cú pháp: thiết lập phụ thuộc B0 => B1,B2"]

        elif cmd.startswith("thiết lập"):
            bits = cmd.replace("thiết lập", "").strip()
            result = [self.register.set_bits_from_string(bits)]

        elif cmd == "reset thanh ghi":
            result = [self.register.reset_register()]

        elif cmd == "lưu phụ thuộc":
            result = [self.register.save_dependencies()]

        elif cmd == "tải phụ thuộc":
            result = [self.register.load_dependencies()]

        else:
            result = ["⚠️ Lệnh không hợp lệ."]

        print("\n".join(result))
        return True