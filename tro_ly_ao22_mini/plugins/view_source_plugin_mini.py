import os
from typing import Any


class ViewPluginSourceHandler:

    def can_handle(self, command: str) ->bool:
        return command.strip().lower().startswith('xem mã plugin ')

    def handle(self, command: str) ->bool:
        plugin_name = command.strip()[len('xem mã plugin '):].strip().replace(
            ' ', '_')
        plugin_filename = f'{plugin_name}.py'
        plugin_path = os.path.join('plugins', plugin_filename)
        if not os.path.exists(plugin_path):
            print(f'❌ Không tìm thấy plugin: {plugin_filename}')
            return True
        try:
            with open(plugin_path, 'r', encoding='utf-8') as f:
                print(f"\n📄 Mã nguồn của '{plugin_filename}':\n")
                print(f.read())
        except Exception as e:
            print(f'⚠️ Lỗi khi đọc plugin: {e}')
        return True


def register(assistant: Any) ->None:
    assistant.handlers.insert(3, ViewPluginSourceHandler())


plugin_info = {'enabled': True, 'register': register, 'command_handle': [
    'xem mã plugin']}
