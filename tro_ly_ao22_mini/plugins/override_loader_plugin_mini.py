"""
Plugin: Custom Plugin Loader
Ghi đè PluginLoader mặc định + loại bỏ plugin blacklist nếu đã load.
"""
import os
import importlib.util
from typing import Dict, Any, List, Callable, Optional, TypedDict


class PluginInfo(TypedDict, total=(False)):
    enabled: bool
    register: Callable[[Any], None]
    command_handle: Optional[List[str]]


BLACKLIST = ['crud_answers_plugin_mini_a85.py', 'today_plugin_mini_a85.py']
_CUSTOM_LOADER_APPLIED = False


class CustomPluginLoader:

    def __init__(self, plugins_folder: str='plugins'):
        self.plugins_folder = plugins_folder
        os.makedirs(plugins_folder, exist_ok=True)

    def load_plugins(self, assistant: Any) ->None:
        print('🔄 Sử dụng CustomPluginLoader...')
        for filename in os.listdir(self.plugins_folder):
            if not filename.endswith('.py') or filename.startswith('_'):
                continue
            if filename in BLACKLIST or filename == 'custom_loader.py':
                print(f'⏭ Bỏ qua: {filename}')
                continue
            plugin_path = os.path.join(self.plugins_folder, filename)
            try:
                spec = importlib.util.spec_from_file_location(
                    f'plugin_{filename[:-3]}', plugin_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                plugin_info: PluginInfo = getattr(module, 'plugin_info', {})
                if not plugin_info.get('enabled', True):
                    print(f'🚫 Plugin bị tắt: {filename}')
                    continue
                if 'register' in plugin_info and callable(plugin_info[
                    'register']):
                    plugin_info['register'](assistant)
                    print(f'✅ Đã nạp plugin: {filename}')
                else:
                    print(f'⚠️ Plugin {filename} không có hàm register')
            except Exception as e:
                print(f'❌ Lỗi khi nạp plugin {filename}: {e}')


def register(assistant: Any):
    global _CUSTOM_LOADER_APPLIED
    if _CUSTOM_LOADER_APPLIED:
        return
    _CUSTOM_LOADER_APPLIED = True
    print('🔁 Đã ghi đè PluginLoader mặc định ')
    before_count = len(assistant.handlers)
    assistant.handlers = [h for h in assistant.handlers if not any(bl_name.
        replace('.py', '') in type(h).__module__ for bl_name in BLACKLIST)]
    removed_count = before_count - len(assistant.handlers)
    if removed_count > 0:
        print(f'🗑 Đã gỡ {removed_count} plugin trong blacklist đã load trước')
    assistant.loader = CustomPluginLoader(assistant.loader.plugins_folder)


plugin_info: PluginInfo = {'enabled': False, 'register': register}
