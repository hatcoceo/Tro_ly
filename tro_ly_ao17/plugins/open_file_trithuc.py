from pathlib import Path

class TrinhSuaTriThucHandler:
    def __init__(self):
        self.file_path = Path("tri_thuc.txt")

    def can_handle(self, command: str) -> bool:
        return command.strip().lower().startswith("chỉnh tri thức")

    def handle(self, command: str) -> bool:
        if not self.file_path.exists():
            print("❌ Không tìm thấy file tri_thuc.txt.")
            return True

        # Đọc nội dung hiện tại
        with self.file_path.open("r", encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f]

        while True:
            print("\n📄 Nội dung hiện tại:")
            for i, line in enumerate(lines, 1):
                print(f"{i:03d}: {line}")
            
            print("\n🔧 Lệnh có thể dùng:")
            print("  sửa <số dòng> <nội dung mới>")
            print("  xóa <số dòng>")
            print("  thêm <nội dung>")
            print("  lưu")
            print("  thoát")

            user_cmd = input("\n✏️ Nhập lệnh chỉnh sửa: ").strip()

            if user_cmd.lower() == "thoát":
                print("👋 Thoát khỏi trình chỉnh sửa.")
                break

            elif user_cmd.lower() == "lưu":
                with self.file_path.open("w", encoding="utf-8") as f:
                    f.writelines(line + "\n" for line in lines)
                print("💾 Đã lưu thay đổi vào tri_thuc.txt.")

            elif user_cmd.startswith("sửa"):
                try:
                    _, idx, *new_text = user_cmd.split()
                    idx = int(idx) - 1
                    if 0 <= idx < len(lines):
                        lines[idx] = " ".join(new_text)
                        print(f"✅ Đã sửa dòng {idx+1}.")
                    else:
                        print("❌ Số dòng không hợp lệ.")
                except Exception as e:
                    print(f"⚠️ Lỗi khi sửa: {e}")

            elif user_cmd.startswith("xóa"):
                try:
                    _, idx = user_cmd.split()
                    idx = int(idx) - 1
                    if 0 <= idx < len(lines):
                        removed = lines.pop(idx)
                        print(f"🗑️ Đã xóa dòng {idx+1}: {removed}")
                    else:
                        print("❌ Số dòng không hợp lệ.")
                except Exception as e:
                    print(f"⚠️ Lỗi khi xóa: {e}")

            elif user_cmd.startswith("thêm"):
                content = user_cmd[5:].strip()
                if content:
                    lines.append(content)
                    print("➕ Đã thêm dòng mới.")
                else:
                    print("❌ Nội dung thêm không được để trống.")
            else:
                print("⚠️ Lệnh không hợp lệ.")

        return True

plugin_info = {
    "enabled": True,
    "register": lambda assistant: assistant.handlers.insert(1, TrinhSuaTriThucHandler()),
    "methods": [],
    "classes": []
}