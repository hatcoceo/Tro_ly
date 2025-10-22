import os
import ast
import astor
import importlib
import sys

def register(assistant):
    assistant.handlers.insert(1, PluginManager(assistant))

plugin_info = {
    'name': 'PluginManager',
    'enabled': True,
    'register': register,
    'command_handle': ['trạng thái plugin', 'bật plugin', 'tắt plugin']
}

class PluginManager:

    def __init__(self, assistant):
        self.plugin_folder = 'plugins'
        self.assistant = assistant
        self.plugin_handlers = {}  # lưu handler đã đăng ký

    def can_handle(self, command: str) -> bool:
        command = command.lower()
        return (
            command.startswith('bật plugin') or
            command.startswith('tắt plugin') or
            command == 'trạng thái plugin'
        )

    def handle(self, command: str) -> str:
        command = command.lower().strip()

        if command == 'trạng thái plugin':
            return self.show_status()

        action = 'bật' if command.startswith('bật plugin') else 'tắt'
        plugin_target = command.replace(f'{action} plugin', '').strip()
        new_state = True if action == 'bật' else False

        plugin_list = self.get_plugin_list()

        if plugin_target.isdigit():
            idx = int(plugin_target) - 1
            if 0 <= idx < len(plugin_list):
                plugin_target = plugin_list[idx]
            else:
                return "⚠️ Số thứ tự plugin không hợp lệ"

        changed = []
        if plugin_target == 'all':
            changed = self.set_all_plugins(new_state)
            for p in changed:
                self.reload_plugin(p, new_state)
            return f"✅ Đã {action} tất cả plugin: {', '.join(changed)}"
        else:
            success = self.set_plugin_state(plugin_target, new_state)
            if success:
                changed.append(plugin_target)
                self.reload_plugin(plugin_target, new_state)
                return f"✅ Plugin '{plugin_target}' đã được {action} và reload thành công"
            else:
                return f"⚠️ Không tìm thấy hoặc lỗi khi sửa plugin '{plugin_target}'"

    def reload_plugin(self, plugin_name: str, enabled: bool):
        module_name = f'plugins.{plugin_name}'
        # Gỡ handler cũ nếu có
        if plugin_name in self.plugin_handlers:
            try:
                self.assistant.handlers.remove(self.plugin_handlers[plugin_name])
            except ValueError:
                pass
            del self.plugin_handlers[plugin_name]

        if not enabled:
            return  # plugin bị tắt, không reload

        try:
            # reload hoặc import module plugin
            if module_name in sys.modules:
                module = importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)

            # nếu plugin có method register, gọi để đăng ký handler
            if hasattr(module, 'register'):
                module.register(self.assistant)
                # lưu handler đã đăng ký để có thể gỡ khi tắt
                self.plugin_handlers[plugin_name] = module
        except Exception as e:
            print("Lỗi reload plugin:", e)

    def get_plugin_list(self):
        plugin_list = []
        for filename in os.listdir(self.plugin_folder):
            if filename.endswith('.py') and not filename.startswith('_') and filename != 'plugin_manager.py':
                plugin_list.append(filename[:-3])
        return sorted(plugin_list)

    def set_plugin_state(self, plugin_name: str, enabled: bool) -> bool:
        path = os.path.join(self.plugin_folder, f'{plugin_name}.py')
        if not os.path.exists(path):
            return False
        try:
            with open(path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())

            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == 'plugin_info':
                            if isinstance(node.value, ast.Dict):
                                for i, key in enumerate(node.value.keys):
                                    if isinstance(key, ast.Str) and key.s == 'enabled':
                                        node.value.values[i] = ast.NameConstant(enabled)
                                        break
                                else:
                                    node.value.keys.append(ast.Str('enabled'))
                                    node.value.values.append(ast.NameConstant(enabled))

            with open(path, 'w', encoding='utf-8') as f:
                f.write(astor.to_source(tree))
            return True
        except Exception as e:
            print("Lỗi set_plugin_state:", e)
            return False

    def set_all_plugins(self, enabled: bool):
        changed = []
        for filename in os.listdir(self.plugin_folder):
            if filename.endswith('.py') and not filename.startswith('_') and filename != 'plugin_manager.py':
                plugin_name = filename[:-3]
                if self.set_plugin_state(plugin_name, enabled):
                    changed.append(plugin_name)
        return changed

    def show_status(self) -> str:
        plugin_list = self.get_plugin_list()
        if not plugin_list:
            return "📦 Không có plugin nào"
        status_lines = []
        for idx, plugin_name in enumerate(plugin_list, start=1):
            status = self.get_plugin_enabled(plugin_name)
            if status is None:
                continue
            status_lines.append(f"{idx}. {plugin_name}: {'🟢 BẬT' if status else '🔴 TẮT'}")
        return "📦 Trạng thái plugin:\n" + "\n".join(status_lines)

    def get_plugin_enabled(self, plugin_name: str):
        path = os.path.join(self.plugin_folder, f'{plugin_name}.py')
        if not os.path.exists(path):
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == 'plugin_info':
                            if isinstance(node.value, ast.Dict):
                                for k, v in zip(node.value.keys, node.value.values):
                                    if isinstance(k, ast.Str) and k.s == 'enabled':
                                        return isinstance(v, ast.NameConstant) and v.value
            return True
        except:
            return None