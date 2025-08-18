import os


class PythonRunnerHandler:

    def __init__(self, assistant):
        self.assistant = assistant
        self.code_lines = []
        self.indent_level = 0

    def can_handle(self, command: str) ->bool:
        if self.assistant.context.get('collecting_code', False):
            return True
        return command.strip().lower() in ['py', 'python', 'run', 'save']

    def handle(self, command: str) ->None:
        raw_input = self.assistant.context.get('last_raw_input', command)
        if raw_input.strip().lower().startswith('run '):
            filename = raw_input.strip()[4:]
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    code = f.read()
                try:
                    local_vars = {}
                    exec(code, {}, local_vars)
                    if 'result' in local_vars:
                        print('📌 Kết quả:', local_vars['result'])
                except Exception as e:
                    print(f'⚠️ Lỗi khi chạy file {filename}: {e}')
            else:
                print(f'⚠️ Không tìm thấy file: {filename}')
            return
        if raw_input.strip().lower().startswith('save '):
            filename = raw_input.strip()[5:]
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(self.code_lines))
                print(f'💾 Đã lưu code vào {filename}')
            except Exception as e:
                print(f'⚠️ Lỗi khi lưu file: {e}')
            return
        if not self.assistant.context.get('collecting_code', False
            ) and raw_input.strip().lower() in ['py', 'python']:
            print(
                "🔹 Nhập mã Python (gõ 'kết thúc' để chạy, 'save file.py' để lưu, 'run file.py' để chạy file):"
                )
            self.assistant.context['collecting_code'] = True
            self.code_lines.clear()
            self.indent_level = 0
            return
        if raw_input.strip().lower() == 'kết thúc':
            self.assistant.context['collecting_code'] = False
            code = '\n'.join(self.code_lines)
            self.code_lines.clear()
            self.indent_level = 0
            try:
                local_vars = {}
                exec(code, {}, local_vars)
                if 'result' in local_vars:
                    print('📌 Kết quả:', local_vars['result'])
            except Exception as e:
                print(f'⚠️ Lỗi khi chạy Python: {e}')
            return
        if self.indent_level > 0:
            raw_input = ' ' * (self.indent_level * 4) + raw_input
        self.code_lines.append(raw_input)
        if raw_input.strip().endswith(':'):
            self.indent_level += 1
        elif raw_input.strip() == '' and self.indent_level > 0:
            self.indent_level -= 1


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


plugin_info = {'enabled': False, 'register': lambda assistant: (setattr(
    assistant, 'run', lambda : self_run_with_raw_capture(assistant)),
    assistant.handlers.append(PythonRunnerHandler(assistant))),
    'command_handle': ['py', 'python', 'run', 'save']}
