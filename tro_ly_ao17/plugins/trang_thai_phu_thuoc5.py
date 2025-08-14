plugin_info = {
    "enabled": False,
    "name": "Register Table Simulator",
    "version": "1.0",
    "description": "Plugin mô phỏng bảng thanh ghi nhiều hàng, 8 bit, thao tác như bảng Excel.",
    "register": lambda assistant: assistant.handlers.insert(1, RegisterTableHandler(assistant)),
    "methods": [],
    "classes": []
}

from typing import Dict, List
from __main__ import ICommandHandler
import pandas as pd

class RegisterTable:
    def __init__(self):
        self.registers: Dict[str, List[int]] = {}
        self.dependencies: Dict[str, List[str]] = {}

    def add_rows(self, count: int):
        start_index = len(self.registers)
        for i in range(count):
            name = f"R{start_index + i}"
            self.registers[name] = [0]*8

    def view_register(self, reg: str = None) -> List[str]:
        if reg:
            if reg not in self.registers:
                return [f"❌ Không tìm thấy thanh ghi {reg}"]
            bits = self.registers[reg]
            return [f"{reg}: {''.join(map(str, bits))}"]
        else:
            result = ["🧮 Bảng thanh ghi:"]
            for name, bits in self.registers.items():
                result.append(f"{name}: {''.join(map(str, bits))}")
            return result

    def set_register(self, reg: str, value: str) -> List[str]:
        if reg not in self.registers:
            return [f"❌ Không tồn tại {reg}"]
        if len(value) != 8 or not set(value).issubset({"0", "1"}):
            return [f"⚠️ Giá trị không hợp lệ (phải là chuỗi nhị phân 8 bit)"]
        self.registers[reg] = [int(b) for b in value]
        return [f"✅ Đã thiết lập {reg} = {value}"]

    def toggle_bit(self, reg: str, bit: int, value: int) -> List[str]:
        if reg not in self.registers:
            return [f"❌ Không tồn tại {reg}"]
        if not (0 <= bit < 8):
            return [f"⚠️ Bit phải từ 0 đến 7"]
        self.registers[reg][bit] = value
        result = [f"🔁 {reg}.B{bit} => {value}"]
        # propagate
        key = f"{reg}.B{bit}"
        visited = set()

        def propagate(k):
            for dep in self.dependencies.get(k, []):
                if dep in visited:
                    continue
                visited.add(dep)
                dep_reg, dep_bit = dep.split(".B")
                self.registers[dep_reg][int(dep_bit)] = value
                result.append(f"➡️ {dep} => {value}")
                propagate(dep)

        propagate(key)
        return result

    def reset(self):
        for k in self.registers:
            self.registers[k] = [0]*8

    def set_dependency(self, src: str, targets: List[str]) -> List[str]:
        if src not in self.dependencies:
            self.dependencies[src] = []
        self.dependencies[src].extend(targets)
        return [f"🔗 {src} => {', '.join(targets)}"]

    def export_to_excel(self, filename="registers.xlsx") -> str:
        df = pd.DataFrame.from_dict(self.registers, orient="index", columns=[f"B{i}" for i in range(7, -1, -1)])
        df.index.name = "Thanh ghi"
        df.to_excel(filename)
        return f"📁 Đã lưu bảng vào file {filename}"


class RegisterTableHandler(ICommandHandler):
    def __init__(self, assistant):
        self.assistant = assistant
        self.table = RegisterTable()

    def can_handle(self, command: str) -> bool:
        keywords = ["thêm dòng", "xem", "thiết lập", "bật bit", "tắt bit", "reset", "lưu bảng"]
        return any(command.startswith(k) for k in keywords)

    def handle(self, command: str) -> bool:
        if command.startswith("thêm dòng"):
            try:
                n = int(command.split()[-1])
                self.table.add_rows(n)
                print(f"✅ Đã thêm {n} dòng")
            except:
                print("⚠️ Lỗi cú pháp: thêm dòng 3")
        elif command.startswith("xem tất cả"):
            print("\n".join(self.table.view_register()))
        elif command.startswith("xem "):
            reg = command.split("xem", 1)[1].strip().upper()
            print("\n".join(self.table.view_register(reg)))
        elif command.startswith("thiết lập phụ thuộc"):
            # ví dụ: thiết lập phụ thuộc R1.B3 => R2.B4,R3.B0
            try:
                _, rule = command.split("phụ thuộc", 1)
                src, targets = rule.strip().split("=>")
                src = src.strip().upper()
                targets = [t.strip().upper() for t in targets.strip().split(",")]
                print("\n".join(self.table.set_dependency(src, targets)))
            except:
                print("⚠️ Lỗi cú pháp phụ thuộc")
        elif command.startswith("thiết lập"):
            # thiết lập R1 = 10101010
            try:
                _, rest = command.split("thiết lập", 1)
                reg, val = rest.strip().split("=")
                reg = reg.strip().upper()
                val = val.strip()
                print("\n".join(self.table.set_register(reg, val)))
            except:
                print("⚠️ Lỗi cú pháp: thiết lập R1 = 01010101")
        elif command.startswith("bật bit"):
            try:
                parts = command.split("của")
                bit = int(parts[0].strip().split("bit")[1])
                reg = parts[1].strip().upper()
                print("\n".join(self.table.toggle_bit(reg, bit, 1)))
            except:
                print("⚠️ Lỗi cú pháp: bật bit 3 của R0")
        elif command.startswith("tắt bit"):
            try:
                parts = command.split("của")
                bit = int(parts[0].strip().split("bit")[1])
                reg = parts[1].strip().upper()
                print("\n".join(self.table.toggle_bit(reg, bit, 0)))
            except:
                print("⚠️ Lỗi cú pháp: tắt bit 5 của R1")
        elif command.startswith("reset thanh ghi"):
            self.table.reset()
            print("🔄 Đã reset tất cả thanh ghi")
        elif command.startswith("lưu bảng"):
            print(self.table.export_to_excel())
        else:
            return False
        return True