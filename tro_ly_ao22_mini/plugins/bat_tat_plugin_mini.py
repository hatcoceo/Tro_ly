import os
import ast
import astor


def register(assistant):
    assistant.handlers.insert(1, PluginManager())


plugin_info = {'name': 'PluginManager', 'enabled': False,  'register':
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
        if plugin_target == 'all':
            changed = self.set_all_plugins(new_state)
            print(f"✅ Đã {action} tất cả plugin: {', '.join(changed)}")
        else:
            success = self.set_plugin_state(plugin_target, new_state)
            if success:
                print(f"✅ Plugin '{plugin_target}' đã được {action}")
            else:
                print(
                    f"⚠️ Không tìm thấy hoặc lỗi khi sửa plugin '{plugin_target}'"
                    )

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
                                    if isinstance(key, ast.Str
                                        ) and key.s == 'enabled':
                                        node.value.values[i] = ast.NameConstant(
                                            enabled)
                                        break
                                else:
                                    node.value.keys.append(ast.Str('enabled'))
                                    node.value.values.append(ast.
                                        NameConstant(enabled))
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
        for filename in os.listdir(self.plugin_folder):
            if filename.endswith('.py') and not filename.startswith('_'):
                plugin_name = filename[:-3]
                status = self.get_plugin_enabled(plugin_name)
                if status is None:
                    continue
                print(f" - {plugin_name}: {'🟢 BẬT' if status else '🔴 TẮT'}")

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
                                    if isinstance(k, ast.Str
                                        ) and k.s == 'enabled':
                                        return isinstance(v, ast.NameConstant
                                            ) and v.value
            return True
        except:
            return None
