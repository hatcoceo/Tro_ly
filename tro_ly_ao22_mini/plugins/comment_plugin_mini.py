import os
import shutil
from typing import Any
plugin_info = {'enabled': False, 'register': lambda assistant: assistant.
    handlers.append(PluginCommentToggleHandler(assistant)),
    'command_handle': ['enable', 'disable']}


class PluginCommentToggleHandler:

    def __init__(self, assistant: Any):
        self.assistant = assistant
        self.plugins_folder = assistant.loader.plugins_folder
        self.backup_folder = os.path.join(self.plugins_folder, '.backup')
        os.makedirs(self.backup_folder, exist_ok=True)

    def can_handle(self, command: str) ->bool:
        return command.startswith('enable ') or command.startswith('disable ')

    def handle(self, command: str) ->None:
        parts = command.split(maxsplit=1)
        if len(parts) < 2:
            print('⚠️ Cú pháp: enable <plugin> hoặc disable <plugin>')
            return
        action, plugin_name = parts[0], parts[1]
        plugin_file = os.path.join(self.plugins_folder, f'{plugin_name}.py')
        if not os.path.exists(plugin_file):
            print(f"❌ Plugin '{plugin_name}' không tồn tại!")
            return
        if action == 'disable':
            self.comment_plugin(plugin_name, plugin_file)
        elif action == 'enable':
            self.uncomment_plugin(plugin_name, plugin_file)

    def comment_plugin(self, name: str, path: str) ->None:
        backup_path = os.path.join(self.backup_folder, f'{name}.py')
        if not os.path.exists(backup_path):
            shutil.copy2(path, backup_path)
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        commented_lines = []
        for line in lines:
            if not line.strip().startswith('#'):
                commented_lines.append('# ' + line)
            else:
                commented_lines.append(line)
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(commented_lines)
        print(
            f"✅ Đã comment toàn bộ plugin '{name}'. Khởi động lại trợ lý để áp dụng."
            )

    def uncomment_plugin(self, name: str, path: str) ->None:
        backup_path = os.path.join(self.backup_folder, f'{name}.py')
        if not os.path.exists(backup_path):
            print(
                f"⚠️ Không tìm thấy bản gốc của plugin '{name}'. Không thể khôi phục."
                )
            return
        shutil.copy2(backup_path, path)
        print(
            f"✅ Đã khôi phục plugin '{name}' từ bản gốc. Khởi động lại trợ lý để áp dụng."
            )
