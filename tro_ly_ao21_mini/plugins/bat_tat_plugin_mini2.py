import os
import re
import sys

def register(assistant):
    assistant.handlers.insert(1, BatTatPlugin())

plugin_info = {
    "name": "BatTatPlugin",
    "enabled": True,
    "register": register
}

class BatTatPlugin:
    def __init__(self):
        self.plugins_folder = "plugins"
        self.this_file = os.path.basename(__file__).replace(".py", "")

    def can_handle(self, command: str) -> bool:
        return (
            command.startswith("bật plugin") or 
            command.startswith("tắt plugin") or 
            command == "trạng thái plugin"
        )

    def handle(self, command: str) -> None:
        command = command.strip().lower()

        if command == "trạng thái plugin":
            plugins = self.get_all_plugins_status()
            print("📦 Danh sách plugin:")
            for i, (name, status) in enumerate(plugins):
                icon = "🟢" if status else "🔴"
                print(f"{i+1}. {name}: {icon} {'BẬT' if status else 'TẮT'}")

            choice = input("👉 Nhập số thứ tự plugin để bật/tắt (Enter để bỏ qua): ").strip()
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(plugins):
                    plugin_name, current_status = plugins[index]
                    new_status = not current_status
                    if self.set_plugin_state(plugin_name, new_status):
                        print(f"✅ Đã {'bật' if new_status else 'tắt'} plugin '{plugin_name}'")
                        self.restart_program()
                    else:
                        print(f"⚠️ Không thể cập nhật plugin '{plugin_name}'")
                else:
                    print("⚠️ Số thứ tự không hợp lệ.")
            else:
                print("👉 Bỏ qua.")
            return

        is_enable = command.startswith("bật plugin")
        plugin_target = command.replace("bật plugin", "").replace("tắt plugin", "").strip()

        if plugin_target == "all":
            changed = self.set_all_plugins_state(is_enable)
            if changed:
                print(f"✅ Đã {'bật' if is_enable else 'tắt'} {len(changed)} plugin: {', '.join(changed)}")
                self.restart_program()
            else:
                print("⚠️ Không có plugin nào được thay đổi.")
        else:
            success = self.set_plugin_state(plugin_target, is_enable)
            if success:
                print(f"✅ Plugin '{plugin_target}' đã được {'bật' if is_enable else 'tắt'}")
                self.restart_program()
            else:
                print(f"⚠️ Không tìm thấy hoặc lỗi khi xử lý plugin '{plugin_target}'")

    def set_plugin_state(self, plugin_name: str, enabled: bool) -> bool:
        if plugin_name == self.this_file:
            return False  # Không tự tắt chính nó

        path = os.path.join(self.plugins_folder, f"{plugin_name}.py")
        if not os.path.isfile(path):
            return False

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            pattern = r"plugin_info\s*=\s*{[^}]*}"
            match = re.search(pattern, content, re.DOTALL)
            if not match:
                return False

            old_info = match.group(0)
            if '"enabled"' in old_info:
                new_info = re.sub(r'"enabled"\s*:\s*(True|False)', f'"enabled": {enabled}', old_info)
            else:
                new_info = old_info[:-1] + f', "enabled": {enabled}' + '}'

            if new_info == old_info:
                return False  # Không có thay đổi

            new_content = content.replace(old_info, new_info)
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return True
        except Exception as e:
            print(f"⚠️ Lỗi sửa plugin {plugin_name}: {e}")
            return False

    def set_all_plugins_state(self, enabled: bool):
        changed = []
        for filename in os.listdir(self.plugins_folder):
            if not filename.endswith(".py") or filename.startswith("_"):
                continue
            plugin_name = filename[:-3]
            if plugin_name == self.this_file:
                continue
            if self.set_plugin_state(plugin_name, enabled):
                changed.append(plugin_name)
        return changed

    def get_plugin_enabled_status(self, plugin_name: str) -> bool:
        path = os.path.join(self.plugins_folder, f"{plugin_name}.py")
        if not os.path.isfile(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            match = re.search(r'"enabled"\s*:\s*(True|False)', content)
            if match:
                return match.group(1) == "True"
            return True  # Nếu không có "enabled", mặc định là bật
        except:
            return False

    def get_all_plugins_status(self):
        plugins = []
        for filename in os.listdir(self.plugins_folder):
            if not filename.endswith(".py") or filename.startswith("_"):
                continue
            plugin_name = filename[:-3]
            status = self.get_plugin_enabled_status(plugin_name)
            plugins.append((plugin_name, status))
        return plugins

    def restart_program(self):
        print("🔄 Đang khởi động lại chương trình để cập nhật plugin...")
        python = sys.executable
        os.execv(python, [python] + sys.argv)