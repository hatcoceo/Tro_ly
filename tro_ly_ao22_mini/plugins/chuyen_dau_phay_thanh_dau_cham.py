import os
import shutil

class ConvertDecimalHandler:
    def can_handle(self, command: str) -> bool:
        return command.startswith("convert ")

    def handle(self, command: str) -> None:
        try:
            # Lấy đường dẫn file
            file_path = command.replace("convert ", "").strip()

            if not os.path.exists(file_path):
                print("❌ File không tồn tại!")
                return

            # Backup file
            backup_path = file_path + ".bak"
            shutil.copy(file_path, backup_path)
            print(f"💾 Đã backup: {backup_path}")

            # Đọc nội dung
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Chuyển đổi dấu phẩy -> dấu chấm
            new_lines = []
            for line in lines:
                new_line = line.replace(",", ".")
                new_lines.append(new_line)

            # Ghi lại file
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

            print("✅ Đã chuyển đổi thành công!")
            print("📊 Ví dụ:")
            print("129,8 -> 129.8")

        except Exception as e:
            print(f"⚠️ Lỗi: {e}")


# Đăng ký plugin
def register(assistant):
    assistant.handlers.append(ConvertDecimalHandler())


plugin_info = {
    "enabled": True,
    "register": register,
    "command_handle": ["convert bieu_do.txt"]
}