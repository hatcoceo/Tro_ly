import os
import ast
import astor
import sys
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning, module='astor')


def register(assistant):
    assistant.handlers.append(PluginManager())


plugin_info = {'name': 'PluginManager', 'enabled': True, 'register':
    register, 'command_handle': ['trạng thái plugin', 'bật plugin',
    'tắt plugin']}


class PluginManager:

    def __init__(self):
        self.plugin_folder = 'plugins'

    def can_handle(self, command: str) ->bool:
        command = command.lower()
        return command.startswith('bật plugin') or command.startswith(
            'tắt plugin') or command == 'trạng thái plugin'

    def handle(self, command: str) ->None:
        command = command.lower().strip()
        if command == 'trạng thái plugin':
            self.show_status()
            return
        action = 'bật' if command.startswith('bật plugin') else 'tắt'
        plugin_target = command.replace(f'{action} plugin', '').strip()
        new_state = True if action == 'bật' else False
        plugin_list = self.get_plugin_list()
        if plugin_target.isdigit():
            idx = int(plugin_target) - 1
            if 0 <= idx < len(plugin_list):
                plugin_target = plugin_list[idx]
            else:
                print('⚠️ Số thứ tự plugin không hợp lệ')
                return
        changed = []
        if plugin_target == 'all':
            changed = self.set_all_plugins(new_state)
            print(f"✅ Đã {action} tất cả plugin: {', '.join(changed)}")
        else:
            success = self.set_plugin_state(plugin_target, new_state)
            if success:
                changed.append(plugin_target)
                print(f"✅ Plugin '{plugin_target}' đã được {action}")
            else:
                print(
                    f"⚠️ Không tìm thấy hoặc lỗi khi sửa plugin '{plugin_target}'"
                    )
        if changed:
            print('🔄 Đang khởi động lại để áp dụng thay đổi...')
            python = sys.executable
            os.execv(python, [python] + sys.argv)

    def get_plugin_list(self):
        plugin_list = []
        for filename in os.listdir(self.plugin_folder):
            if filename.endswith('.py') and not filename.startswith('_'
                ) and filename != 'plugin_manager.py':
                plugin_list.append(filename[:-3])
        return sorted(plugin_list)

    def set_plugin_state(self, plugin_name: str, enabled: bool) ->bool:
        path = os.path.join(self.plugin_folder, f'{plugin_name}.py')
        if not os.path.exists(path):
            return False
        try:
            with open(path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name
                            ) and target.id == 'plugin_info':
                            if isinstance(node.value, ast.Dict):
                                for i, key in enumerate(node.value.keys):
                                    if isinstance(key, ast.Constant
                                        ) and isinstance(key.value, str
                                        ) and key.value == 'enabled':
                                        node.value.values[i] = ast.Constant(enabled
                                            )
                                        break
                                else:
                                    node.value.keys.append(ast.Constant(
                                        'enabled'))
                                    node.value.values.append(ast.Constant(
                                        enabled))
            with open(path, 'w', encoding='utf-8') as f:
                f.write(astor.to_source(tree))
            return True
        except Exception as e:
            print(f'⚠️ Lỗi sửa plugin {plugin_name}: {e}')
            return False

    def set_all_plugins(self, enabled: bool):
        changed = []
        for filename in os.listdir(self.plugin_folder):
            if filename.endswith('.py') and not filename.startswith('_'
                ) and filename != 'plugin_manager.py':
                plugin_name = filename[:-3]
                if self.set_plugin_state(plugin_name, enabled):
                    changed.append(plugin_name)
        return changed

    def show_status(self):
        print('📦 Trạng thái plugin:')
        plugin_list = self.get_plugin_list()
        for idx, plugin_name in enumerate(plugin_list, start=1):
            status = self.get_plugin_enabled(plugin_name)
            if status is None:
                continue
            print(f"{idx}. {plugin_name}: {'🟢 BẬT' if status else '🔴 TẮT'}")

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
                        if isinstance(target, ast.Name
                            ) and target.id == 'plugin_info':
                            if isinstance(node.value, ast.Dict):
                                for k, v in zip(node.value.keys, node.value
                                    .values):
                                    if isinstance(k, ast.Constant
                                        ) and isinstance(k.value, str
                                        ) and k.value == 'enabled':
                                        return isinstance(v, ast.Constant
                                            ) and v.value
            return True
        except:
            return None
