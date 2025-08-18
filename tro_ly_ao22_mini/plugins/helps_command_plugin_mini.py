import os
import importlib.util


class HelpHandler:

    def __init__(self, assistant):
        self.assistant = assistant
        self.plugins_folder = assistant.loader.plugins_folder

    def can_handle(self, command: str) ->bool:
        return command in ['help', 'trợ giúp', 'lệnh']

    def handle(self, command: str) ->None:
        print('📘 Danh sách lệnh khả dụng:')
        for filename in os.listdir(self.plugins_folder):
            if not filename.endswith('.py') or filename.startswith('_'):
                continue
            plugin_path = os.path.join(self.plugins_folder, filename)
            try:
                spec = importlib.util.spec_from_file_location(
                    f'plugin_{filename[:-3]}', plugin_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                plugin_info = getattr(module, 'plugin_info', None)
                if plugin_info and plugin_info.get('enabled', True):
                    commands = plugin_info.get('command_handle', [])
                    if commands:
                        print(f" - {filename[:-3]}: {', '.join(commands)}")
            except Exception as e:
                print(f'⚠️ Không thể đọc {filename}: {e}')


def register(assistant) ->None:
    assistant.handlers.insert(1, HelpHandler(assistant))


plugin_info = {'enabled': True, 'register': register, 'command_handle': [
    'help', 'trợ giúp', 'lệnh']}
