import os
import sys
import importlib.util


class PluginLoader2:

    def __init__(self, plugins_folder: str='plugins2'):
        self.plugins_folder = plugins_folder
        os.makedirs(plugins_folder, exist_ok=True)

    def load_plugins(self, assistant):
        for filename in os.listdir(self.plugins_folder):
            if not filename.endswith('.py') or filename.startswith('_'):
                continue
            plugin_path = os.path.join(self.plugins_folder, filename)
            try:
                spec = importlib.util.spec_from_file_location(
                    f'plugin2_{filename[:-3]}', plugin_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                plugin_info = getattr(module, 'plugin_info', {})
                if not plugin_info.get('enabled', True):
                    continue
                if 'register' in plugin_info and callable(plugin_info[
                    'register']):
                    plugin_info['register'](assistant)
            except Exception as e:
                print(f'⚠️ Error loading plugin2 {filename}: {e}')


class VirtualAssistant2:

    def __init__(self):
        self.handlers = []
        self.loader = PluginLoader2()
        self.context = {}

    def process_command(self, command: str) ->bool:
        command = command.strip().lower()
        if command in ['exit', 'quit', 'thoát']:
            print('👋 Tạm biệt từ Asi-2!')
            return False
        for handler in self.handlers:
            if hasattr(handler, 'can_handle') and handler.can_handle(command):
                handler.handle(command)
                return True
        print('🤷 Asi-2 không hiểu lệnh đó.')
        return True

    def run(self):
        print('🤖 Xin chào, tôi là trợ lý ảo thứ hai (Asi-2)')
        print("Nhập 'exit' để thoát. \n")
        self.loader.load_plugins(self)
        while True:
            try:
                user_input = input('Asi-2: ')
                if not self.process_command(user_input):
                    break
            except KeyboardInterrupt:
                print('\n👋 Tạm biệt từ Asi-2!')
                break
            except Exception as e:
                print(f'⚠️ Error: {e}')


def register(assistant):
    print('🔁 Đang khởi chạy trợ lý mới: Asi-2 ...')
    asi2 = VirtualAssistant2()
    asi2.run()
    sys.exit(0)


plugin_info = {'name': 'Asi-2 Override Without Multiprocessing', 'enabled':
    False, 'register': register}
