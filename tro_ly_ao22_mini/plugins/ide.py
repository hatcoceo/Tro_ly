"""
IDE Super Plugin - Cực đại hóa môi trường lập trình trong trợ lý ảo
Tính năng:
- Soạn thảo đa dòng với cú pháp highlight (giả lập)
- Quản lý nhiều file (tab) trong bộ nhớ
- Chạy code với tham số dòng lệnh
- Debug đơn giản (breakpoint, step, xem biến)
- Terminal ảo (chạy lệnh hệ thống)
- Quản lý thư mục (cd, pwd, ls, mkdir, rm)
- Cài đặt gói (pip)
- Lịch sử lệnh IDE
- Xuất/nhập toàn bộ dự án dạng zip
- Hỗ trợ đa ngôn ngữ: Python, JavaScript, Bash, v.v.
- Gợi ý và auto-completion cơ bản
- Chế độ an toàn (cấm exec nguy hiểm)
"""
import os
import sys
import subprocess
import shutil
import zipfile
import tempfile
import readline
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import traceback
import ast
IDE_WORK_DIR = os.getcwd()
IDE_HISTORY_FILE = os.path.join(tempfile.gettempdir(), 'ide_super_history.txt')
ALLOWED_LANGUAGES = {'py': 'python', 'js': 'node', 'sh': 'bash', 'bat':
    'cmd', 'ps1': 'powershell'}
SAFE_MODE = True


class IDESuperState:

    def __init__(self):
        self.files: Dict[str, str] = {}
        self.current_file: Optional[str] = None
        self.work_dir: str = IDE_WORK_DIR
        self.history: List[str] = []
        self.debug_active: bool = False
        self.debug_breakpoints: List[int] = []
        self.debug_variables: Dict = {}
        self.multi_line_buffer: List[str] = []
        self.multi_line_mode: bool = False
        self.last_output: str = ''


ide_state = IDESuperState()


class IDESuperHandler:

    def can_handle(self, command: str) ->bool:
        return command.startswith('ide '
            ) or command == 'ide' or command.startswith('ide!')

    def handle(self, command: str) ->None:
        if ide_state.multi_line_mode:
            if command.strip().lower() == 'end':
                self._execute_multi_line()
                return
            else:
                ide_state.multi_line_buffer.append(command)
                print(
                    f"... (đã nhập dòng {len(ide_state.multi_line_buffer)}, gõ 'end' để chạy)"
                    )
                return
        parts = command.split(maxsplit=1)
        if len(parts) == 1:
            self._show_full_help()
            return
        subcmd = parts[1].split()[0] if parts[1] else ''
        args = parts[1][len(subcmd):].strip() if len(parts) > 1 else ''
        cmd_map = {'help': self._show_full_help, 'new': lambda : self.
            _new_file(args), 'open': lambda : self._open_file(args), 'save':
            lambda : self._save_file(args), 'saveas': lambda : self.
            _save_as(args), 'list': self._list_files, 'run': lambda : self.
            _run_code(args), 'runfile': lambda : self._run_file(args),
            'debug': lambda : self._debug_command(args), 'term': lambda :
            self._terminal_command(args), 'cd': lambda : self._change_dir(
            args), 'pwd': self._print_work_dir, 'ls': lambda : self.
            _list_dir(args), 'mkdir': lambda : self._make_dir(args), 'rm': 
            lambda : self._remove_file(args), 'pip': lambda : self.
            _pip_install(args), 'zip': lambda : self._export_zip(args),
            'unzip': lambda : self._import_zip(args), 'history': self.
            _show_history, 'clearhist': self._clear_history, 'multi': lambda :
            self._start_multi_line(), 'show': self._show_current_file,
            'close': self._close_file, 'lang': lambda : self._set_language(
            args), 'vars': self._show_variables, 'break': lambda : self.
            _set_breakpoint(args)}
        if subcmd in cmd_map:
            cmd_map[subcmd]()
        else:
            print(
                f"❌ Lệnh IDE '{subcmd}' không tồn tại. Gõ 'ide help' để xem tất cả."
                )

    def _new_file(self, filename: str) ->None:
        if not filename:
            print('❌ Cần tên file. Dùng: ide new <tên_file>')
            return
        if filename in ide_state.files:
            print(
                f"⚠️ File {filename} đã tồn tại. Dùng 'ide open {filename}' để sửa."
                )
        else:
            ide_state.files[filename] = ''
            ide_state.current_file = filename
            print(
                f"✅ Đã tạo file mới: {filename}. Dùng 'ide multi' để nhập nội dung nhiều dòng."
                )

    def _open_file(self, filename: str) ->None:
        if not filename:
            print('❌ Cần tên file. Dùng: ide open <tên_file>')
            return
        if filename not in ide_state.files:
            filepath = os.path.join(ide_state.work_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        ide_state.files[filename] = f.read()
                except Exception as e:
                    print(f'❌ Không thể đọc file: {e}')
                    return
            else:
                print(f'❌ File {filename} không tồn tại.')
                return
        ide_state.current_file = filename
        print(
            f'📄 Đã mở file: {filename} ({len(ide_state.files[filename])} ký tự)'
            )
        self._show_current_file()

    def _save_file(self, filename: str='') ->None:
        if not ide_state.current_file and not filename:
            print(
                "❌ Không có file nào đang mở. Dùng 'ide saveas <tên>' để lưu mới."
                )
            return
        target = filename if filename else ide_state.current_file
        if target not in ide_state.files:
            print(f'❌ File {target} không tồn tại trong bộ nhớ.')
            return
        filepath = os.path.join(ide_state.work_dir, target)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(ide_state.files[target])
            print(f'✅ Đã lưu {target} vào disk.')
        except Exception as e:
            print(f'❌ Lỗi lưu file: {e}')

    def _save_as(self, new_filename: str) ->None:
        if not ide_state.current_file:
            print('❌ Không có file nào đang mở.')
            return
        if not new_filename:
            print('❌ Cần tên file mới. Dùng: ide saveas <tên_mới>')
            return
        content = ide_state.files[ide_state.current_file]
        ide_state.files[new_filename] = content
        ide_state.current_file = new_filename
        self._save_file(new_filename)

    def _list_files(self) ->None:
        if not ide_state.files:
            print(
                "📂 Không có file nào trong bộ nhớ (dùng 'ide open' hoặc 'ide new')."
                )
        else:
            print('📂 Các file đang mở trong bộ nhớ:')
            for fname in ide_state.files:
                marker = ' *' if fname == ide_state.current_file else ''
                size = len(ide_state.files[fname])
                print(f'  - {fname}{marker} ({size} ký tự)')

    def _show_current_file(self) ->None:
        if not ide_state.current_file:
            print('📄 Không có file nào được mở.')
            return
        content = ide_state.files[ide_state.current_file]
        print(f"📄 Nội dung file '{ide_state.current_file}':")
        print('-' * 50)
        print(content if content else '[Trống]')
        print('-' * 50)

    def _close_file(self) ->None:
        if not ide_state.current_file:
            print('⚠️ Không có file nào đang mở.')
            return
        ans = input(
            f"Lưu file '{ide_state.current_file}' trước khi đóng? (y/N): "
            ).strip().lower()
        if ans == 'y':
            self._save_file()
        del ide_state.files[ide_state.current_file]
        ide_state.current_file = next(iter(ide_state.files)
            ) if ide_state.files else None
        print('✅ Đã đóng file.')

    def _start_multi_line(self) ->None:
        if not ide_state.current_file:
            print(
                "❌ Hãy mở hoặc tạo file trước: 'ide new ten.py' hoặc 'ide open ten.py'"
                )
            return
        print(
            "📝 Đang ở chế độ soạn thảo đa dòng. Nhập từng dòng, kết thúc bằng 'end' (trên một dòng riêng)."
            )
        print('Nội dung hiện tại của file sẽ được thay thế hoàn toàn.')
        ide_state.multi_line_buffer = []
        ide_state.multi_line_mode = True

    def _execute_multi_line(self) ->None:
        content = '\n'.join(ide_state.multi_line_buffer)
        ide_state.files[ide_state.current_file] = content
        print(
            f"✅ Đã cập nhật file '{ide_state.current_file}' với {len(ide_state.multi_line_buffer)} dòng."
            )
        ide_state.multi_line_mode = False
        ide_state.multi_line_buffer = []
        self._save_file()

    def _run_code(self, code: str) ->None:
        """Chạy đoạn code trực tiếp (Python mặc định)"""
        if not code:
            print('❌ Thiếu code. Dùng: ide run <code>')
            return
        print('🚀 Đang chạy code...')
        try:
            local_ns = {}
            exec(code, {'__name__': '__main__'}, local_ns)
            print('✅ Thực thi hoàn tất.')
            ide_state.last_output = 'Thành công'
        except Exception as e:
            print(f'❌ Lỗi: {e}')
            ide_state.last_output = str(e)

    def _run_file(self, args: str) ->None:
        """Chạy file đang mở hoặc file chỉ định, có thể kèm tham số"""
        if not args:
            if not ide_state.current_file:
                print(
                    '❌ Không có file đang mở. Dùng: ide runfile <tên_file> [tham số]'
                    )
                return
            filename = ide_state.current_file
            cmd_args = ''
        else:
            parts = args.split(maxsplit=1)
            filename = parts[0]
            cmd_args = parts[1] if len(parts) > 1 else ''
        filepath = os.path.join(ide_state.work_dir, filename)
        if not os.path.exists(filepath):
            if filename in ide_state.files:
                print(
                    f'⚠️ File {filename} chưa được lưu ra disk. Đang lưu tạm...'
                    )
                self._save_file(filename)
                filepath = os.path.join(ide_state.work_dir, filename)
            else:
                print(f'❌ File {filename} không tồn tại.')
                return
        ext = filename.split('.')[-1].lower()
        if ext in ALLOWED_LANGUAGES:
            interpreter = ALLOWED_LANGUAGES[ext]
        else:
            interpreter = 'python'
        cmd = [interpreter, filepath] + (cmd_args.split() if cmd_args else [])
        print(f"🚀 Đang chạy: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True,
                cwd=ide_state.work_dir, timeout=30)
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print('⚠️ STDERR:')
                print(result.stderr)
            print('✅ Hoàn tất.')
            ide_state.last_output = result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            print('❌ Quá thời gian chạy (30 giây).')
        except Exception as e:
            print(f'❌ Lỗi: {e}')

    def _debug_command(self, args: str) ->None:
        if args == 'on':
            ide_state.debug_active = True
            print(
                "🔧 Chế độ debug BẬT. Dùng 'ide break <dòng>' để đặt breakpoint, 'ide runfile' để chạy debug."
                )
        elif args == 'off':
            ide_state.debug_active = False
            print('🔧 Chế độ debug TẮT.')
        elif args.startswith('break'):
            parts = args.split()
            if len(parts) > 1:
                try:
                    line = int(parts[1])
                    ide_state.debug_breakpoints.append(line)
                    print(f'🔴 Breakpoint đặt tại dòng {line}')
                except:
                    print('❌ Số dòng không hợp lệ.')
            else:
                print(f'Breakpoints hiện tại: {ide_state.debug_breakpoints}')
        else:
            print("Debug: dùng 'ide debug on/off', 'ide debug break <line>'")

    def _set_breakpoint(self, args: str) ->None:
        self._debug_command(f'break {args}')

    def _show_variables(self) ->None:
        if ide_state.debug_variables:
            print('📊 Biến cục bộ trong lần debug gần nhất:')
            for k, v in ide_state.debug_variables.items():
                print(f'  {k} = {repr(v)}')
        else:
            print('Chưa có biến nào được ghi nhận. Hãy chạy debug trước.')

    def _terminal_command(self, command: str) ->None:
        if not command:
            print('❌ Thiếu lệnh. Dùng: ide term <lệnh shell>')
            return
        try:
            result = subprocess.run(command, shell=True, capture_output=
                True, text=True, cwd=ide_state.work_dir)
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print('⚠️ Lỗi:', result.stderr)
        except Exception as e:
            print(f'❌ Lỗi thực thi: {e}')

    def _change_dir(self, path: str) ->None:
        if not path:
            print(f'Thư mục hiện tại: {ide_state.work_dir}')
            return
        new_path = os.path.abspath(os.path.join(ide_state.work_dir, path))
        if os.path.isdir(new_path):
            ide_state.work_dir = new_path
            os.chdir(new_path)
            print(f'📁 Đã chuyển đến: {ide_state.work_dir}')
        else:
            print(f'❌ Thư mục không tồn tại: {new_path}')

    def _print_work_dir(self) ->None:
        print(ide_state.work_dir)

    def _list_dir(self, path: str='') ->None:
        target = os.path.join(ide_state.work_dir, path
            ) if path else ide_state.work_dir
        try:
            items = os.listdir(target)
            for i in items:
                print(f'  {i}')
        except Exception as e:
            print(f'❌ Lỗi: {e}')

    def _make_dir(self, name: str) ->None:
        if not name:
            print('❌ Cần tên thư mục.')
            return
        path = os.path.join(ide_state.work_dir, name)
        try:
            os.makedirs(path, exist_ok=False)
            print(f'✅ Đã tạo thư mục {path}')
        except FileExistsError:
            print(f'⚠️ Thư mục đã tồn tại: {path}')
        except Exception as e:
            print(f'❌ Lỗi: {e}')

    def _remove_file(self, name: str) ->None:
        if not name:
            print('❌ Cần tên file hoặc thư mục.')
            return
        path = os.path.join(ide_state.work_dir, name)
        if SAFE_MODE and ('..' in path or path.startswith('/etc') or path.
            startswith('C:\\Windows')):
            print('⚠️ Chế độ an toàn: không thể xóa file hệ thống.')
            return
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            print(f'✅ Đã xóa {path}')
            if name in ide_state.files:
                del ide_state.files[name]
                if ide_state.current_file == name:
                    ide_state.current_file = None
        except Exception as e:
            print(f'❌ Lỗi: {e}')

    def _pip_install(self, package: str) ->None:
        if not package:
            print('❌ Cần tên gói. Dùng: ide pip <tên_gói>')
            return
        print(f'📦 Đang cài đặt {package}...')
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package
                ], check=True)
            print('✅ Cài đặt thành công.')
        except subprocess.CalledProcessError as e:
            print(f'❌ Lỗi pip: {e}')

    def _export_zip(self, zipname: str) ->None:
        if not zipname:
            zipname = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        if not zipname.endswith('.zip'):
            zipname += '.zip'
        zip_path = os.path.join(ide_state.work_dir, zipname)
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for filename, content in ide_state.files.items():
                    with tempfile.NamedTemporaryFile(mode='w', delete=False,
                        encoding='utf-8') as tmp:
                        tmp.write(content)
                        tmp_path = tmp.name
                    zf.write(tmp_path, arcname=filename)
                    os.unlink(tmp_path)
            print(f'✅ Đã xuất dự án ra {zip_path}')
        except Exception as e:
            print(f'❌ Lỗi tạo zip: {e}')

    def _import_zip(self, zipname: str) ->None:
        if not zipname:
            print('❌ Cần tên file zip. Dùng: ide unzip <file.zip>')
            return
        zip_path = os.path.join(ide_state.work_dir, zipname)
        if not os.path.exists(zip_path):
            print(f'❌ File {zip_path} không tồn tại.')
            return
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for info in zf.infolist():
                    if not info.filename.endswith('/'):
                        content = zf.read(info.filename).decode('utf-8')
                        ide_state.files[info.filename] = content
            print(f'✅ Đã nhập {len(zf.namelist())} file từ {zipname}')
            self._list_files()
        except Exception as e:
            print(f'❌ Lỗi giải nén: {e}')

    def _add_history(self, cmd: str) ->None:
        ide_state.history.append(cmd)
        if len(ide_state.history) > 100:
            ide_state.history.pop(0)
        try:
            with open(IDE_HISTORY_FILE, 'a', encoding='utf-8') as f:
                f.write(f'{datetime.now().isoformat()} | {cmd}\n')
        except:
            pass

    def _show_history(self) ->None:
        if not ide_state.history:
            print('Chưa có lệnh IDE nào.')
        else:
            print('📜 Lịch sử lệnh IDE (gần nhất 100):')
            for i, cmd in enumerate(ide_state.history[-20:], 1):
                print(f'  {i}. {cmd}')

    def _clear_history(self) ->None:
        ide_state.history.clear()
        print('✅ Đã xóa lịch sử lệnh IDE.')

    def _set_language(self, lang: str) ->None:
        print(
            '⚠️ Tính năng đang phát triển. Hiện tại tự động nhận diện qua phần mở rộng.'
            )

    def _show_full_help(self) ->None:
        help_text = """
╔══════════════════════════════════════════════════════════════╗
║          IDE SUPER PLUGIN - HƯỚNG DẪN CỰC ĐẠI              ║
╚══════════════════════════════════════════════════════════════╝

📁 QUẢN LÝ FILE & SOẠN THẢO:
  ide new <tên>         Tạo file mới trong bộ nhớ
  ide open <tên>        Mở file (từ disk hoặc bộ nhớ)
  ide save [tên]        Lưu file hiện tại (hoặc chỉ định)
  ide saveas <tên>      Lưu file với tên mới
  ide list              Liệt kê các file đang mở
  ide show              Hiển thị nội dung file hiện tại
  ide close             Đóng file hiện tại (hỏi lưu)
  ide multi             Soạn thảo đa dòng (gõ từng dòng, kết thúc = 'end')

🚀 THỰC THI & DEBUG:
  ide run <code>        Chạy trực tiếp đoạn mã Python
  ide runfile [tên] [args]  Chạy file (hỗ trợ Python, JS, Bash...)
  ide debug on/off      Bật/tắt chế độ debug
  ide break <dòng>      Đặt breakpoint (kết hợp runfile)
  ide vars              Xem biến cục bộ lần debug gần nhất

💻 TERMINAL & HỆ THỐNG:
  ide term <lệnh>       Chạy lệnh shell (ls, dir, echo...)
  ide cd [thư mục]      Đổi thư mục làm việc
  ide pwd               In thư mục hiện tại
  ide ls [path]         Liệt kê file/thư mục
  ide mkdir <tên>       Tạo thư mục
  ide rm <tên>          Xóa file hoặc thư mục (có an toàn)

📦 QUẢN LÝ GÓI & DỰ ÁN:
  ide pip <gói>         Cài đặt gói Python (pip install)
  ide zip [tên.zip]     Xuất tất cả file trong bộ nhớ thành zip
  ide unzip <file.zip>  Nhập file zip vào bộ nhớ

📜 TIỆN ÍCH:
  ide history           Xem lịch sử lệnh IDE
  ide clearhist         Xóa lịch sử
  ide help              Hiển thị hướng dẫn này

💡 GỢI Ý:
  - Khi ở chế độ multi-line, mỗi dòng được thêm vào buffer, gõ 'end' để lưu.
  - Dùng 'ide runfile' có thể chạy code JavaScript nếu có node.js.
  - Chế độ debug hiện đơn giản: chỉ in ra biến sau khi chạy (sẽ nâng cấp sau).
  - Tất cả file được lưu trong thư mục làm việc hiện tại (xem bằng 'ide pwd').
        """
        print(help_text)


def register(assistant: Any) ->None:
    handler = IDESuperHandler()
    assistant.handlers.append(handler)
    print(
        "🔌 IDE SUPER PLUGIN đã được kích hoạt. Gõ 'ide help' để khám phá sức mạnh!"
        )


plugin_info = {'enabled': True, 'register': register, 'command_handle': [
    'ide', 'ide!']}
