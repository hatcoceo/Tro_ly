import os
import importlib.util
import inspect
from typing import Any

plugin_info = {
    "enabled": False,
    "methods": [],
    "classes": [],
}

class ListFunctionsHandler:
    def can_handle(self, command: str) -> bool:
        return command.strip().lower() == "liệt kê hàm"

    def handle(self, command: str) -> bool:
        print("\n📦 Đang liệt kê các hàm trong hệ thống...\n")

        target_folders = [
            ".",  # mã chính (file chính)
            "plugins",
            "version_managers",
            "interfaces",
            "assistants",
            "virtualassistantcore",
            "process_inputs",
            "run"
        ]

        for folder in target_folders:
            if not os.path.exists(folder):
                continue
            self._list_functions_in_folder(folder)

        return True

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

            # Hàm top-level
            functions = inspect.getmembers(module, inspect.isfunction)
            methods_printed = False
            for func_name, _ in functions:
                print(f"  🔹 Hàm: {func_name}")
                methods_printed = True

            # Lớp và phương thức
            classes = inspect.getmembers(module, inspect.isclass)
            for cls_name, cls_obj in classes:
                if cls_obj.__module__ != module.__name__:
                    continue
                print(f"  🏗️  Lớp: {cls_name}")
                for name, method in inspect.getmembers(cls_obj, inspect.isfunction):
                    print(f"     🔸 Phương thức: {name}")

            if not functions and not classes:
                print("  (Không có hàm/lớp)")

        except Exception as e:
            print(f"❌ Lỗi đọc {filepath}: {e}")

# Đăng ký handler
def register(assistant: Any):
    assistant.handlers.insert (1, ListFunctionsHandler())

plugin_info["register"] = register