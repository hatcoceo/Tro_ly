# macro tương tác 
# có chế độ cài đặt  tự động trả lời trợ lý ( ví dụ yêu cầu người dùng nhập đường Dân Chủ )
# Thêm chế độ đặt biến cho INPUT
import os
import sys
import time
import builtins

macro_folder = 'macros'
os.makedirs(macro_folder, exist_ok=True)
recorder_is_playing = False


class MacroRecorder:
    def __init__(self):
        self.recording = False
        self.commands = []
        self.current_macro_name = None

    def start(self, macro_name):
        if self.recording:
            print(f"⚠️ Đang ghi macro '{self.current_macro_name}'. Dừng lại trước.")
            return
        self.recording = True
        self.commands = []
        self.current_macro_name = macro_name
        print(f'🔴 Bắt đầu ghi macro: {macro_name}')

    def stop(self):
        if not self.recording:
            print('⚠️ Không có macro nào đang được ghi.')
            return
        path = os.path.join(macro_folder, f'{self.current_macro_name}.txt')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.commands))
        print(f'🟢 Đã lưu macro ({len(self.commands)} lệnh) vào: {path}')
        self.recording = False
        self.commands = []
        self.current_macro_name = None

    def record(self, command: str):
        if self.recording and not recorder_is_playing and command.strip() and not command.startswith(('ghi macro ', 'dừng ghi macro', 'chạy macro ')):
            self.commands.append(command.strip())


recorder = MacroRecorder()


class MacroCommandHandler:
    def __init__(self, assistant):
        self.assistant = assistant
        self._original_input = sys.stdin
        self._install_input_hook()

    def _install_input_hook(self):
        class MacroInputWrapper:
            def __init__(self, original):
                self.original = original
            def readline(self):
                user_input = self.original.readline()
                recorder.record(user_input)
                return user_input
        sys.stdin = MacroInputWrapper(sys.stdin)

    def can_handle(self, command: str) -> bool:
        return command.startswith(('ghi macro ', 'dừng ghi macro', 'chạy macro '))

    def handle(self, command: str) -> bool:
        if command.startswith('ghi macro '):
            recorder.start(command[10:].strip())
            return True
        elif command == 'dừng ghi macro':
            recorder.stop()
            return True
        elif command.startswith('chạy macro '):
            rest = command[11:].strip()
            if not rest:
                print('❌ Thiếu tên macro.')
                return True
            delay = 1.0
            macro_name = rest
            if ' ' in rest:
                try:
                    possible_delay = rest.split()[-1]
                    delay = float(possible_delay)
                    macro_name = rest[:rest.rfind(possible_delay)].strip()
                except ValueError:
                    delay = 1.0
            self._play_macro(macro_name, delay)
            return True
        return False

    def _play_macro(self, macro_name, delay=1.0):
        global recorder_is_playing
        path = os.path.join(macro_folder, f'{macro_name}.txt')
        if not os.path.exists(path):
            print(f'❌ Không tìm thấy macro: {macro_name}')
            return

        print(f'🏃 Đang chạy macro: {macro_name} (delay: {delay:.1f}s)')
        recorder_is_playing = True

        variables = {}          # Lưu các biến (từ SET hoặc ?)
        auto_input_queue = []   # Hàng đợi trả lời tự động cho input()

        original_input = builtins.input
        def auto_input(prompt=''):
            if auto_input_queue:
                answer = auto_input_queue.pop(0)
                print(f'{prompt}{answer}')
                return answer
            else:
                return original_input(prompt)

        try:
            builtins.input = auto_input
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    cmd = line.strip()
                    if not cmd:
                        continue

                    # --- Lệnh INPUT: thêm vào queue, hỗ trợ biến {tên} ---
                    if cmd.startswith('INPUT '):
                        value = cmd[6:].strip()
                        # Thay thế biến (ví dụ {bid} -> giá trị)
                        for key, val in variables.items():
                            value = value.replace(f'{{{key}}}', str(val))
                        # Bỏ dấu ngoặc kép bao ngoài nếu có
                        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        auto_input_queue.append(value)
                        continue

                    # --- Lệnh SET: tạo biến ---
                    if cmd.startswith('SET '):
                        parts = cmd[4:].split('=', 1)
                        if len(parts) == 2:
                            var_name = parts[0].strip()
                            var_value = parts[1].strip()
                            # Bỏ dấu ngoặc kép nếu có
                            if (var_value.startswith('"') and var_value.endswith('"')) or (var_value.startswith("'") and var_value.endswith("'")):
                                var_value = var_value[1:-1]
                            variables[var_name] = var_value
                        continue

                    # --- Câu hỏi tương tác của macro: ? ... ---
                    if cmd.startswith('? '):
                        rest = cmd[2:].strip()
                        auto_answer = None
                        if ' auto:' in rest:
                            parts = rest.split(' auto:', 1)
                            question = parts[0].strip()
                            auto_answer = parts[1].strip()
                            if (auto_answer.startswith('"') and auto_answer.endswith('"')) or (auto_answer.startswith("'") and auto_answer.endswith("'")):
                                auto_answer = auto_answer[1:-1]
                            # Thay thế biến trong auto_answer
                            auto_answer = auto_answer.format(**variables)
                        else:
                            question = rest

                        if auto_answer is not None:
                            user_input = auto_answer
                            print(f'🤖 (tự động) {question}\n👉 {user_input}')
                        else:
                            user_input = original_input(f'\n🤖 {question}\n👉 ')
                        variables['answer'] = user_input
                        print()
                        continue

                    # --- Lệnh thường: thay thế biến và gửi ---
                    for key, val in variables.items():
                        cmd = cmd.replace(f'{{{key}}}', str(val))
                    print(f'⏩ {cmd}')
                    self.assistant.process_command(cmd)
                    time.sleep(delay)
        finally:
            builtins.input = original_input
            recorder_is_playing = False


# Định nghĩa plugin_info theo cấu trúc của trợ lý Asi-86
plugin_info = {
    'enabled': True,
    'register': lambda assistant: assistant.handlers.append(MacroCommandHandler(assistant)),
    'methods': [],
    'classes': [MacroRecorder, MacroCommandHandler],
    'description': 'Ghi và chạy macro, hỗ trợ INPUT {biến}, ? auto:, SET biến, {answer}'
}