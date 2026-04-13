import os
import shutil
from typing import Any, List
DEFAULT_STORAGE = '/sdcard' if os.path.exists('/sdcard') else os.getcwd()
current_dir = DEFAULT_STORAGE if os.access(DEFAULT_STORAGE, os.R_OK
    ) else os.getcwd()


def safe_path(path: str) ->str:
    """Đảm bảo không truy cập ra ngoài vùng cho phép (tuỳ chọn)."""
    full = os.path.abspath(os.path.join(current_dir, path))
    return full


def _find_case_insensitive(base_dir: str, name: str) ->(str | None):
    """Tìm file/thư mục có tên (không phân biệt hoa thường) trong base_dir.
    Trả về tên đúng case nếu tìm thấy duy nhất, ngược lại trả về None."""
    try:
        items = os.listdir(base_dir)
    except (FileNotFoundError, PermissionError):
        return None
    lower_name = name.lower()
    matches = [item for item in items if item.lower() == lower_name]
    if len(matches) == 1:
        return matches[0]
    return None


def resolve_path(raw_path: str) ->str:
    """Chuyển đường dẫn có thể viết thường thành đường dẫn đúng case thực tế.
    Hỗ trợ cả đường dẫn tương đối và tuyệt đối."""
    global current_dir
    if not raw_path or raw_path.strip() == '':
        return current_dir
    if os.path.isabs(raw_path):
        parts = raw_path.split(os.sep)
        root = os.sep
        start_idx = 1
    else:
        parts = raw_path.split(os.sep)
        root = current_dir
        start_idx = 0
    current = root
    for i in range(start_idx, len(parts)):
        part = parts[i]
        if part == '' or part == '.':
            continue
        if part == '..':
            current = os.path.dirname(current)
            continue
        found_name = _find_case_insensitive(current, part)
        if found_name:
            current = os.path.join(current, found_name)
        else:
            current = os.path.join(current, part)
    return current


class StorageHandler:

    def can_handle(self, command: str) ->bool:
        cmd = command.strip().split()[0].lower()
        return cmd in {'ls', 'dir', 'cd', 'pwd', 'cat', 'rm', 'mkdir',
            'rename', 'cp', 'copy', 'mv', 'move', 'info', 'tree'}

    def handle(self, command: str) ->None:
        global current_dir
        parts = command.strip().split()
        if not parts:
            return
        cmd = parts[0].lower()
        args = parts[1:]
        try:
            if cmd in ('ls', 'dir'):
                path = args[0] if args else '.'
                self._list(path)
            elif cmd == 'cd':
                target = args[0] if args else '/'
                self._cd(target)
            elif cmd == 'pwd':
                print(f'📂 {current_dir}')
            elif cmd == 'cat':
                if not args:
                    print('⚠️ Cần tên file: cat <file>')
                else:
                    self._cat(args[0])
            elif cmd == 'rm':
                if not args:
                    print('⚠️ Cần đường dẫn: rm <file_or_dir>')
                else:
                    self._rm(args[0])
            elif cmd == 'mkdir':
                if not args:
                    print('⚠️ Cần tên thư mục: mkdir <name>')
                else:
                    self._mkdir(args[0])
            elif cmd == 'rename':
                if len(args) < 2:
                    print('⚠️ Cần 2 đối số: rename <old> <new>')
                else:
                    self._rename(args[0], args[1])
            elif cmd in ('cp', 'copy'):
                if len(args) < 2:
                    print('⚠️ Cần 2 đối số: cp <src> <dst>')
                else:
                    self._copy(args[0], args[1])
            elif cmd in ('mv', 'move'):
                if len(args) < 2:
                    print('⚠️ Cần 2 đối số: mv <src> <dst>')
                else:
                    self._move(args[0], args[1])
            elif cmd == 'info':
                if not args:
                    print('⚠️ Cần đường dẫn: info <path>')
                else:
                    self._info(args[0])
            elif cmd == 'tree':
                self._tree(args[0] if args else '.')
        except Exception as e:
            print(f'❌ Lỗi: {e}')

    def _list(self, path: str):
        target = resolve_path(path)
        if not os.path.exists(target):
            print(f'❌ Không tồn tại: {target}')
            return
        if os.path.isfile(target):
            print(f'📄 {os.path.basename(target)}')
            return
        items = os.listdir(target)
        items.sort()
        for item in items:
            full = os.path.join(target, item)
            if os.path.isdir(full):
                print(f'📁 {item}/')
            else:
                print(f'📄 {item}')
        print(f'\nTổng: {len(items)} mục')

    def _cd(self, path: str):
        global current_dir
        new_dir = resolve_path(path)
        if os.path.isdir(new_dir):
            current_dir = new_dir
        else:
            print(f'❌ Không phải thư mục: {new_dir}')

    def _cat(self, file: str):
        target = resolve_path(file)
        if not os.path.isfile(target):
            print(f'❌ Không phải file: {target}')
            return
        try:
            with open(target, 'r', encoding='utf-8') as f:
                print(f.read())
        except UnicodeDecodeError:
            print('⚠️ File nhị phân, không thể hiển thị dạng text.')

    def _rm(self, path: str):
        target = resolve_path(path)
        if not os.path.exists(target):
            print(f'❌ Không tồn tại: {target}')
            return
        if os.path.isfile(target):
            os.remove(target)
            print(f'✅ Đã xoá file: {target}')
        else:
            shutil.rmtree(target)
            print(f'✅ Đã xoá thư mục: {target}')

    def _mkdir(self, name: str):
        target = safe_path(name)
        os.makedirs(target, exist_ok=True)
        print(f'✅ Đã tạo thư mục: {target}')

    def _rename(self, old: str, new: str):
        src = resolve_path(old)
        dst = safe_path(new)
        os.rename(src, dst)
        print(f'✅ Đã đổi tên: {old} → {new}')

    def _copy(self, src: str, dst: str):
        src_path = resolve_path(src)
        dst_path = safe_path(dst)
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        else:
            shutil.copy2(src_path, dst_path)
        print(f'✅ Đã sao chép: {src} → {dst}')

    def _move(self, src: str, dst: str):
        src_path = resolve_path(src)
        dst_path = safe_path(dst)
        shutil.move(src_path, dst_path)
        print(f'✅ Đã di chuyển: {src} → {dst}')

    def _info(self, path: str):
        target = resolve_path(path)
        if not os.path.exists(target):
            print(f'❌ Không tồn tại: {target}')
            return
        stat = os.stat(target)
        size = stat.st_size
        if os.path.isdir(target):
            size_str = f' (chứa {len(os.listdir(target))} mục)'
        else:
            size_str = f' ({size} bytes)'
        print(f'📌 {target}')
        print(f"   Loại: {'Thư mục' if os.path.isdir(target) else 'Tập tin'}")
        print(f'   Kích thước: {size_str}')
        print(f'   Lần sửa cuối: {stat.st_mtime}')

    def _tree(self, path: str, prefix: str='', is_last: bool=True):
        target = resolve_path(path)
        if not os.path.isdir(target):
            print(f'❌ Không phải thư mục: {target}')
            return
        items = os.listdir(target)
        items.sort()
        for i, item in enumerate(items):
            full = os.path.join(target, item)
            connector = '└── ' if i == len(items) - 1 else '├── '
            print(prefix + connector + item)
            if os.path.isdir(full):
                extension = '    ' if i == len(items) - 1 else '│   '
                self._tree(full, prefix + extension, i == len(items) - 1)


plugin_info = {'enabled': True, 'register': lambda assistant: assistant.
    handlers.append(StorageHandler())}
