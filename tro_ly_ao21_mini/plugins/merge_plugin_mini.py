# plugins/merge_plugin.py
#sd: gộp plugin a vào b dòng 10
import os
class MergePluginHandler:
    def can_handle(self, command: str) -> bool:
        return command.startswith("gộp plugin ")

    def handle(self, command: str) -> None:
        try:
            # Câu lệnh: gộp plugin <plugin_nguon> vào <plugin_dich> dòng <dòng>
            parts = command.split()
            if len(parts) < 6 or parts[3] != "vào" or parts[5] != "dòng":
                print("❌ Cú pháp sai. Dùng: gộp plugin <nguon> vào <dich> dòng <số>")
                return

            plugin_src = parts[2].strip()
            plugin_dest = parts[4].strip()
            line_number = int(parts[6])

            src_path = os.path.join("plugins", f"{plugin_src}.py")
            dest_path = os.path.join("plugins", f"{plugin_dest}.py")

            if not os.path.exists(src_path):
                print(f"❌ Plugin nguồn '{plugin_src}' không tồn tại.")
                return
            if not os.path.exists(dest_path):
                print(f"❌ Plugin đích '{plugin_dest}' không tồn tại.")
                return

            with open(src_path, 'r', encoding='utf-8') as f:
                src_lines = f.readlines()

            with open(dest_path, 'r', encoding='utf-8') as f:
                dest_lines = f.readlines()

            # Đảm bảo số dòng hợp lệ
            if line_number < 1 or line_number > len(dest_lines) + 1:
                print(f"❌ Dòng {line_number} không hợp lệ trong '{plugin_dest}.py'.")
                return

            # Gộp
            new_lines = dest_lines[:line_number - 1] + ['\n# --- Start Merged Content ---\n'] + src_lines + ['\n# --- End Merged Content ---\n'] + dest_lines[line_number - 1:]

            with open(dest_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

            print(f"✅ Đã gộp '{plugin_src}.py' vào '{plugin_dest}.py' tại dòng {line_number}.")

        except Exception as e:
            print(f"⚠️ Lỗi khi gộp plugin: {e}")

def register(assistant):
    assistant.handlers.insert (1, MergePluginHandler())
plugin_info = {
    "name": "merge_plugin",
    "enabled": True,
    "register": register 
}
