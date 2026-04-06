from openpyxl import Workbook, load_workbook
import os
import matplotlib.pyplot as plt

class ExcelProHandler:
    def __init__(self, assistant):
        self.file = "excel_crud_demo.xlsx"
        self.assistant = assistant
        # Dictionary ánh xạ action -> phương thức xử lý
        self.action_map = {
            "create": self.create,
            "add": self.add,
            "read": self.read,
            "update": self.update,
            "delete": self.delete,
            "delrows": self.delete_rows_range,  
            "delcolrange": self.delete_column_range,
            "find": self.find,
            "avg": self.avg,
            "chart": self.chart,
            "auto": self.auto_decision,
            "avg_range": self.avg_range
        }

    def can_handle(self, command: str) -> bool:
        return command.startswith("excel")

    def handle(self, command: str):
        try:
            parts = command.split()
            action = parts[1] if len(parts) > 1 else ""

            # Tra cứu phương thức trong dictionary
            method = self.action_map.get(action)
            if method:
                method(parts)   # Gọi phương thức với parts
            else:
                print("❌ Lệnh không hợp lệ")

        except Exception as e:
            print(f"⚠️ Lỗi: {e}")

    # ================= BASIC =================

    def create(self, parts=None):
        wb = Workbook()
        ws = wb.active
        wb.save(self.file)
        print("✅ Created file")

    def add(self, parts):
        # Lấy dữ liệu từ parts[2:]
        data = parts[2:]
        wb = self._load()
        if not wb: return
        ws = wb.active

        row = []
        for x in data:
            try:
                row.append(float(x))
            except:
                row.append(x)

        ws.append(row)
        wb.save(self.file)
        print(f"✅ Added: {row}")

    def read(self, parts=None):
        wb = self._load()
        if not wb: return
        ws = wb.active

        for r in ws.iter_rows(values_only=True):
            print(r)

    def update(self, parts):
        if len(parts) < 5:
            print("⚠️ excel update row col value")
            return

        wb = self._load()
        if not wb: return
        ws = wb.active

        r, c = int(parts[2]), int(parts[3])
        val = parts[4]

        ws.cell(row=r, column=c).value = val
        wb.save(self.file)
        print("✅ Updated")

    def delete(self, parts):
        if len(parts) < 3:
            return

        wb = self._load()
        if not wb: return
        ws = wb.active

        ws.delete_rows(int(parts[2]))
        wb.save(self.file)
        print("🗑 Deleted")

    # ================= QUERY =================

    def find(self, parts):
        if len(parts) < 3:
            return

        keyword = parts[2]
        wb = self._load()
        if not wb: return
        ws = wb.active

        for row in ws.iter_rows(values_only=True):
            if any(keyword in str(cell) for cell in row):
                print("🔍", row)

    def avg(self, parts=None):
        wb = self._load()
        if not wb: return
        ws = wb.active

        nums = []
        for row in ws.iter_rows(values_only=True):
            for cell in row:
                if isinstance(cell, (int, float)):
                    nums.append(cell)

        if nums:
            avg = sum(nums) / len(nums)
            self.assistant.context["avg"] = avg
            print(f"📊 AVG = {avg}")
        else:
            print("⚠️ No numbers")

    # ================= CHART =================

    def chart(self, parts=None):
        wb = self._load()
        if not wb: return
        ws = wb.active

        data = []
        for row in ws.iter_rows(values_only=True):
            for cell in row:
                if isinstance(cell, (int, float)):
                    data.append(cell)

        if not data:
            print("⚠️ No data")
            return

        plt.figure()
        plt.plot(data)
        plt.title("Excel Data Chart")
        plt.savefig("chart.png")
        plt.close()

        print("📈 Saved chart.png")

    # ================= AI DECISION =================

    def auto_decision(self, parts=None):
        wb = self._load()
        if not wb: return
        ws = wb.active

        data = []
        for row in ws.iter_rows(values_only=True):
            for cell in row:
                if isinstance(cell, (int, float)):
                    data.append(cell)

        if len(data) < 2:
            print("⚠️ Not enough data")
            return

        avg = sum(data[:-1]) / len(data[:-1])  # bỏ số cuối
        last = data[-1]

        print(f"AVG (no last): {avg}")
        print(f"Last: {last}")

        if last < avg:
            decision = "BUY"
        else:
            decision = "WAIT"

        print(f"🤖 Decision: {decision}")

        # lưu vào context
        self.assistant.context["decision"] = decision

    # ================= UTILS =================

    def _load(self):
        if not os.path.exists(self.file):
            print("⚠️ File not found")
            return None
        return load_workbook(self.file)

    def avg_range(self, parts):
        if len(parts) < 5:
            print("⚠️ excel avg_range <col> <start_row> <end_row>")
            return

        wb = self._load()
        if not wb: return
        ws = wb.active

        col = int(parts[2])
        start = int(parts[3])
        end = int(parts[4])

        nums = []

        for r in range(start, end + 1):
            val = ws.cell(row=r, column=col).value

            try:
                nums.append(float(val))
            except:
                continue

        if nums:
            avg = sum(nums) / len(nums)
            print(f"📊 AVG (col {col}, rows {start}-{end}) = {avg}")
            self.assistant.context["avg_range"] = avg
        else:
            print("⚠️ No numeric data in range")
    
    # Thêm phương thức xóa nhiều hàng
    def delete_rows_range(self, parts):
        if len(parts) < 4:
            print("⚠️ excel delrows <start_row> <end_row>")
            return
        wb = self._load()
        if not wb: return
        ws = wb.active
        start = int(parts[2])
        end = int(parts[3])
        # Tính số hàng cần xóa
        count = end - start + 1
        ws.delete_rows(start, count)
        wb.save(self.file)
        print(f"🗑 Deleted rows {start} to {end}")
    
    # Thêm phương thức xóa ô trong cột theo khoảng hàng
    def delete_column_range(self, parts):
        if len(parts) < 5:
            print("⚠️ excel delcolrange <col> <start_row> <end_row>")
            return
        wb = self._load()
        if not wb: return
        ws = wb.active
        col = int(parts[2])
        start = int(parts[3])
        end = int(parts[4])
        for row in range(start, end + 1):
            ws.cell(row=row, column=col).value = None
        wb.save(self.file)
        print(f"🗑 Cleared column {col}, rows {start} to {end}")

# ================= REGISTER =================

def register(assistant):
    assistant.handlers.append(ExcelProHandler(assistant))


plugin_info = {
    "enabled": True,
    "register": register,
    "command_handle": ["excel create", "excel add apple banana orange", "excel update 2 1 hello", "excel delete 2", "excel read", "excel avg_range 1 2 3"]
}