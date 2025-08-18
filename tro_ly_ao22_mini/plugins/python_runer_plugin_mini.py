class PythonRunnerHandler:

    def __init__(self, assistant):
        self.assistant = assistant
        self.code_lines = []

    def can_handle(self, command: str) ->bool:
        if self.assistant.context.get('collecting_code', False):
            return True
        return command.strip().lower() in ['py', 'python']

    def handle(self, command: str) ->None:
        raw_input = self.assistant.context.get('last_raw_input', command)
        if not self.assistant.context.get('collecting_code', False):
            print("🔹 Nhập mã Python (gõ 'kết thúc' để chạy):")
            self.assistant.context['collecting_code'] = True
            self.code_lines.clear()
            return
        if raw_input.strip().lower() == 'kết thúc':
            self.assistant.context['collecting_code'] = False
            code = '\n'.join(self.code_lines)
            self.code_lines.clear()
            try:
                local_vars = {}
                exec(code, {}, local_vars)
                if 'result' in local_vars:
                    print('📌 Kết quả:', local_vars['result'])
            except Exception as e:
                print(f'⚠️ Lỗi khi chạy Python: {e}')
            return
        self.code_lines.append(raw_input)


plugin_info = {'enabled': False, 'register': lambda assistant: (setattr(
    assistant, 'original_run_input', getattr(assistant, 'run', None)),
    setattr(assistant, 'run', lambda : self_run_with_raw_capture(assistant)
    ), assistant.handlers.append(PythonRunnerHandler(assistant))),
    'command_handle': ['py', 'python']}


def self_run_with_raw_capture(assistant):
    print('🤖 Xin chào, tôi là trợ lý ảo (Asi-1)')
    print("Nhập 'exit' để thoát. \n")
    while True:
        try:
            user_input = input('Bạn: ')
            assistant.context['last_raw_input'] = user_input
            if not assistant.process_command(user_input):
                break
        except KeyboardInterrupt:
            print('\n👋 Tạm biệt!')
            break
        except Exception as e:
            print(f'⚠️ Lỗi: {e}')
