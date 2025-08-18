import os
import subprocess
import tempfile
import shutil


class CMultilineCodeRunner:

    def __init__(self):
        self.collecting = False
        self.lines = []

    def can_handle(self, command: str) ->bool:
        return command.startswith('bắt đầu c') or self.collecting

    def handle(self, command: str) ->None:
        if command.strip() == 'bắt đầu c':
            self.collecting = True
            self.lines = []
            print("📝 Nhập mã C, gõ 'kết thúc' để chạy.")
            return
        if command.strip() == 'kết thúc':
            self.collecting = False
            code = '\n'.join(self.lines)
            self.run_c_code(code)
            self.lines = []
            return
        if self.collecting:
            self.lines.append(command)
        else:
            print('⚠️ Không hiểu lệnh.')

    def run_c_code(self, code: str) ->None:
        with tempfile.TemporaryDirectory() as tmpdir:
            c_file = os.path.join(tmpdir, 'main.c')
            exe_file = os.path.join(tmpdir, 'main_exec')
            with open(c_file, 'w') as f:
                f.write(code)
            gcc_path = shutil.which('gcc')
            if gcc_path is None:
                print(
                    "❌ Không tìm thấy 'gcc'. Bạn cần cài 'Pydroid C/C++ Plugin'."
                    )
                return
            compile_result = subprocess.run([gcc_path, c_file, '-o',
                exe_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True)
            if compile_result.returncode != 0:
                print('❌ Lỗi biên dịch:')
                print(compile_result.stderr)
                return
            print('🚀 Kết quả thực thi:')
            run_result = subprocess.run([exe_file], stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True)
            if run_result.stdout:
                print(run_result.stdout)
            if run_result.stderr:
                print('⚠️ stderr:')
                print(run_result.stderr)


plugin_info = {'enabled': False, 'register': lambda assistant: assistant.
    handlers.append(CMultilineCodeRunner()), 'command_handle': ['bắt đầu c']}
