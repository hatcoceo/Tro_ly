import os
import importlib.util
import inspect
import builtins
import sys
from types import ModuleType

plugin_info = {
    "enabled": False,
    "methods": [],
    "classes": [],
}

class ListAllFunctionsHandler:
    def can_handle(self, command: str) -> bool:
        return command.strip().lower() == "liệt kê tất cả hàm"

    def handle(self, command: str) -> bool:
        print("\n📦 Đang liệt kê các hàm trong hệ thống và thư viện chuẩn...\n")

        self._list_builtin_functions()
        self._list_standard_library_functions()
        self._list_project_functions()

        return True

    def _list_builtin_functions(self):
        print("\n=== 🧠 Built-in Functions ===")
        for name in dir(builtins):
            obj = getattr(builtins, name)
            if inspect.isbuiltin(obj) or inspect.isfunction(obj):
                try:
                    file = inspect.getfile(obj)
                    lineno = inspect.getsourcelines(obj)[1]
                    print(f"🔹 {name}  📍 {file}:{lineno}")
                except:
                    print(f"🔹 {name}  📍 [built-in]")

    def _list_standard_library_functions(self):
        stdlib_modules = [
            'os', 'sys', 're', 'math', 'datetime', 'random', 'itertools', 'functools',
            'json', 'time', 'collections', 'typing', 'pathlib', 'threading', 'subprocess'
        ]
        print("\n=== 🧰 Standard Library Modules ===")
        for module_name in stdlib_modules:
            try:
                module = importlib.import_module(module_name)
                print(f"\n📦 Module: {module_name}")
                funcs = inspect.getmembers(module, inspect.isfunction)
                for name, func_obj in funcs:
                    try:
                        file = inspect.getfile(func_obj)
                        lineno = inspect.getsourcelines(func_obj)[1]
                        print(f"  🔸 {name}  📍 {file}:{lineno}")
                    except:
                        print(f"  🔸 {name}  📍 [vị trí không xác định]")
            except Exception as e:
                print(f"⚠️ Không thể import module {module_name}: {e}")

    def _list_project_functions(self):
        print("\n=== 🏗️ Hàm Tự Tạo Trong Dự Án ===")
        target_folders = [
            ".", "plugins", "version_managers", "interfaces",
            "assistants", "virtualassistantcore", "process_inputs", "run"
        ]

        for folder in target_folders:
            if not os.path.exists(folder):
                continue
            self._list_functions_in_folder(folder)

    def _list_functions_in_folder(self, folder: str) -> None:
        for filename in os.listdir(folder):
            if filename.endswith(".py") and not filename.startswith("__"):
                filepath = os.path.join(folder, filename)
                self._list_functions_in_file(filepath, folder)

    def _list_functions_in_file(self, filepath: str, folder: str) -> None:
        try:
            spec = importlib.util.spec_from_file_location("temp_module", filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            print(f"\n📁 File: {os.path.relpath(filepath)}")

            functions = inspect.getmembers(module, inspect.isfunction)
            for func_name, func_obj in functions:
                try:
                    file = inspect.getfile(func_obj)
                    lineno = inspect.getsourcelines(func_obj)[1]
                    rel_path = os.path.relpath(file)
                    print(f"  🔹 Hàm: {func_name}  📍 {rel_path}:{lineno}")
                except Exception:
                    print(f"  🔹 Hàm: {func_name}  📍 [vị trí không xác định]")

            classes = inspect.getmembers(module, inspect.isclass)
            for cls_name, cls_obj in classes:
                if cls_obj.__module__ != module.__name__:
                    continue
                print(f"  🏗️  Lớp: {cls_name}")
                for name, method in inspect.getmembers(cls_obj, inspect.isfunction):
                    try:
                        file = inspect.getfile(method)
                        lineno = inspect.getsourcelines(method)[1]
                        rel_path = os.path.relpath(file)
                        print(f"     🔸 Phương thức: {name}  📍 {rel_path}:{lineno}")
                    except Exception:
                        print(f"     🔸 Phương thức: {name}  📍 [vị trí không xác định]")

        except Exception as e:
            print(f"❌ Lỗi đọc {filepath}: {e}")

# Đăng ký
def register(assistant):
    assistant.handlers.insert(1, ListAllFunctionsHandler())

plugin_info["register"] = register