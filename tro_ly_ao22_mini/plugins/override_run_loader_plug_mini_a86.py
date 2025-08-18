from types import MethodType


class CustomLoader:

    def __init__(self, plugins_folder='plugins'):
        self.plugins_folder = plugins_folder

    def load_plugins(self, assistant):
        print('🔍 [CustomLoader] Chỉ load các plugin đặc biệt!')
        pass


def custom_run(self):
    print('🤖 Đây là run() mới từ plugin!')
    print("Nhập 'exit' để thoát.\n")
    while True:
        cmd = input('Bạn: ')
        if cmd.strip().lower() in ['exit', 'quit', 'thoát']:
            print('👋 Tạm biệt!')
            break
        print(f'[Plugin-run] Bạn vừa nhập: {cmd}')


def register(assistant):
    assistant.loader = CustomLoader()
    assistant.loader.load_plugins(assistant)
    assistant.run = MethodType(custom_run, assistant)


plugin_info = {'enabled': False, 'register': register}
