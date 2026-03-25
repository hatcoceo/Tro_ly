import os
import subprocess
import matplotlib
matplotlib.use('Agg')  # 🔥 Quan trọng cho Pydroid (không cần GUI)
import matplotlib.pyplot as plt


class PlotHandler:
    def __init__(self, assistant):
        self.assistant = assistant

    def can_handle(self, command: str) -> bool:
        return command.startswith("plot ")

    def handle(self, command: str) -> None:
        try:
            print("📥 Lệnh:", command)

            content = command.replace("plot ", "").strip()

            # =========================
            # 📂 TRƯỜNG HỢP: đọc từ file
            # =========================
            if os.path.exists(content):
                print("📂 Đọc file:", content)

                with open(content, "r", encoding="utf-8") as f:
                    data = f.read()

                numbers = self.parse_numbers(data)
                self.plot(numbers, title=f"File: {content}")
                return

            # =========================
            # ✏️ TRƯỜNG HỢP: input trực tiếp
            # =========================
            print("✏️ Input:", content)
            numbers = self.parse_numbers(content)

            print("🔢 Parsed:", numbers)

            self.plot(numbers)

        except Exception as e:
            print(f"⚠️ Lỗi: {e}")

    # =========================
    # 🔢 Parse số
    # =========================
    def parse_numbers(self, text: str):
        text = text.replace(",", " ").replace("\n", " ")
        parts = text.split()

        numbers = []
        for p in parts:
            try:
                numbers.append(float(p))
            except:
                pass

        if not numbers:
            raise ValueError("Không tìm thấy số hợp lệ!")

        return numbers

    # =========================
    # 📊 Vẽ biểu đồ
    # =========================
    def plot(self, numbers, title="Biểu đồ"):
        x = list(range(1, len(numbers) + 1))

        plt.figure()
        plt.plot(x, numbers, marker='o')
        plt.title(title)
        plt.xlabel("Index")
        plt.ylabel("Value")
        plt.grid()

        # 🔥 Lưu file
        file_path = os.path.abspath("plot.png")
        plt.savefig(file_path)
        plt.close()

        print(f"📊 Đã lưu biểu đồ: {file_path}")

        # 🔥 Mở ảnh (Android)
        self.open_image(file_path)

    # =========================
    # 📱 Mở ảnh trên Android
    # =========================
    def open_image(self, path: str):
        try:
            subprocess.run(["xdg-open", path])
        except Exception as e:
            print("⚠️ Không mở được ảnh tự động")
            print("👉 Bạn hãy mở file plot.png thủ công")


# =========================
# 🔌 Register plugin
# =========================
def register(assistant):
    assistant.handlers.append(PlotHandler(assistant))


plugin_info = {
    "enabled": True,
    "register": register,
    "command_handle": ["plot 1 2 3 3.1 3.3", "plot bieu_do.txt"]
}