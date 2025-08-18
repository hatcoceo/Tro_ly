import os
import ast
import importlib
import subprocess
import sys
from typing import Any, List


def extract_imports(file_path: str) ->List[str]:
    """Trích xuất tên các thư viện từ file plugin"""
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=file_path)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.split('.')[0])
    return list(set(imports))


def install_missing_modules(modules: List[str]) ->bool:
    """Tự động cài đặt thư viện bị thiếu. Trả về True nếu có cài mới"""
    installed_any = False
    for module in modules:
        if module in sys.builtin_module_names:
            continue
        try:
            importlib.import_module(module)
        except ImportError:
            print(f'📦 Cài đặt thư viện bị thiếu: {module}')
            try:
                subprocess.check_call([sys.executable, '-m', 'pip',
                    'install', module])
                installed_any = True
            except subprocess.CalledProcessError as e:
                print(f'⚠️ Không thể cài đặt {module}: {e}')
    return installed_any


def register(assistant: Any) ->None:
    """Plugin khởi động - xử lý cài đặt các thư viện còn thiếu cho các plugin khác"""
    print('🔍 Đang kiểm tra và cài đặt các thư viện cần thiết cho plugin...')
    plugin_folder = 'plugins'
    current_file = os.path.basename(__file__)
    any_installed = False
    for filename in os.listdir(plugin_folder):
        if not filename.endswith('.py') or filename.startswith('_'
            ) or filename == current_file:
            continue
        plugin_path = os.path.join(plugin_folder, filename)
        imports = extract_imports(plugin_path)
        if install_missing_modules(imports):
            any_installed = True
    print('✅ Thư viện plugin đã được kiểm tra xong.')
    if any_installed:
        print(
            '🔁 Có thư viện mới được cài đặt. Đang khởi động lại chương trình...'
            )
        python = sys.executable
        os.execv(python, [python] + sys.argv)


plugin_info = {'enabled': False, 'register': register, 'command_handle': []}
