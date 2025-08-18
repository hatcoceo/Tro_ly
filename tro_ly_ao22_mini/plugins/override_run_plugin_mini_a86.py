from types import MethodType


def custom_run(self):
    print('🤖 Đây là run() mới từ plugin!')
    print("Nhập 'exit' để thoát.\n")
    while True:
        try:
            cmd = input('Bạn: ')
            if not self.process_command(cmd):
                break
        except KeyboardInterrupt:
            print('\n👋 Goodbye!')
            break
        except Exception as e:
            print(f'⚠️ Error: {e}')


def register(assistant):
    assistant.run = MethodType(custom_run, assistant)


plugin_info = {'enabled': False, 'register': register}
