import os
import importlib.util
import time  # Thêm import này
from abc import ABC, abstractmethod
from typing import List, Callable, Any, Optional, Union

# ==================== INTERFACES ====================

class ICommandHandler(ABC):
    @abstractmethod
    def can_handle(self, command: str) -> bool:
        pass

    @abstractmethod
    def handle(self, command: str) -> bool:
        pass

class IVersionManager(ABC):
    @abstractmethod
    def register_method_version(self, class_name: str, method_name: str, version: str, method_ref: Callable, description: str = "", mode: str = "replace") -> bool:
        pass

    @abstractmethod
    def register_class_version(self, class_name: str, version: str, class_ref: Any) -> bool:
        pass

    @abstractmethod
    def get_method_version(self, class_name: str, method_name: str, version: Union[str, List[str]] = None) -> Optional[Callable]:
        pass

    @abstractmethod
    def get_class_version(self, class_name: str, version: str = None) -> Optional[Any]:
        pass

    @abstractmethod
    def switch_version(self, version: str) -> bool:
        pass

# ==================== VERSION MANAGER ====================

class BaseVersionManager(IVersionManager):
    def __init__(self):
        self.versions = {
            "default": {
                "methods": {},
                "classes": {},
                "description": "Mặc định"
            }
        }
        self.current_version = "default"

    def register_method_version(self, class_name, method_name, version, method_ref, description="", mode="replace"):
        if version not in self.versions:
            self.versions[version] = {"methods": {}, "classes": {}, "description": ""}
        methods = self.versions[version]["methods"].setdefault(class_name, {})

        if mode == "replace" or method_name not in methods:
            methods[method_name] = {
                "function": method_ref,
                "description": description
            }

        elif mode == "append":
            old_func = methods[method_name]["function"]

            def combined_func(*args, **kwargs):
                old_result = old_func(*args, **kwargs)
                new_result = method_ref(*args, **kwargs)
                return (old_result, new_result)

            methods[method_name] = {
                "function": combined_func,
                "description": methods[method_name]["description"] + " + " + description
            }

        elif mode == "multi":
            current_func = methods.get(method_name, {}).get("function")
            if not isinstance(current_func, list):
                current_func = [current_func] if current_func else []
            current_func.append(method_ref)
            methods[method_name] = {
                "function": current_func,
                "description": description
            }

        else:
            raise ValueError(f"Chế độ mode không hợp lệ: {mode}")

        return True

    def register_class_version(self, class_name, version, class_ref):
        if version not in self.versions:
            self.versions[version] = {"methods": {}, "classes": {}, "description": ""}
        self.versions[version]["classes"][class_name] = class_ref
        return True

    def get_method_version(self, class_name, method_name, version: Union[str, List[str]] = None):
        version = version or self.current_version
        if isinstance(version, str):
            version = [version]

        funcs = []
        for ver in version:
            method_info = self.versions.get(ver, {}).get("methods", {}).get(class_name, {}).get(method_name)
            if method_info:
                func = method_info["function"]
                if isinstance(func, list):
                    funcs.extend([(ver, f) for f in func])
                else:
                    funcs.append((ver, func))

        if not funcs:
            return None

        def combined(*args, **kwargs):
            return {ver: f(*args, **kwargs) for ver, f in funcs}

        return combined

    def get_class_version(self, class_name, version=None):
        version = version or self.current_version
        return self.versions.get(version, {}).get("classes", {}).get(class_name)

    def switch_version(self, version):
        if version in self.versions:
            self.current_version = version
            return True
        return False

# ==================== CORE ASSISTANT ====================

class VirtualAssistantCore:
    def __init__(self):
        self.version_manager = BaseVersionManager()
        self.handlers: List[ICommandHandler] = []
        self.context: dict = {}

        self.load_plugins("plugins")

    @property
    def shared_registry(self):
        return self.context.get("shared_registry")

    @property
    def hooks(self):
        return self.context.get("hook_manager")

    def register_before_hook(self, hook_name: str, handler):
        if self.hooks:
            self.hooks.register_before_hook(hook_name, handler)

    def register_after_hook(self, hook_name: str, handler):
        if self.hooks:
            self.hooks.register_after_hook(hook_name, handler)

    def call_before_hooks(self, hook_name: str, *args, **kwargs):
        if self.hooks:
            self.hooks.call_before_hooks(hook_name, *args, **kwargs)

    def call_after_hooks(self, hook_name: str, result=None, *args, **kwargs):
        if self.hooks:
            self.hooks.call_after_hooks(hook_name, result=result, *args, **kwargs)

    def load_plugins(self, folder):
        if not os.path.exists(folder):
            os.makedirs(folder)
            return

        for filename in os.listdir(folder):
            if filename.endswith(".py"):
                path = os.path.join(folder, filename)
                try:
                    spec = importlib.util.spec_from_file_location("plugin_module", path)
                    plugin = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(plugin)
                except Exception as e:
                    print(f"❌ Lỗi plugin {filename}: {e}")
                    continue

                info = getattr(plugin, "plugin_info", None)
                if not info or not info.get("enabled", True):
                    continue

                for method in info.get("methods", []):
                    self.version_manager.register_method_version(
                        method["class_name"], method["method_name"],
                        method["version"], method["function"],
                        method.get("description", ""),
                        method.get("mode", "replace")
                    )
                    print(f"🧩 Đăng ký method: {method['class_name']}.{method['method_name']} ({method['version']}, mode={method.get('mode', 'replace')})")

                for cls in info.get("classes", []):
                    self.version_manager.register_class_version(
                        cls["class_name"], cls["version"], cls["class_ref"]
                    )
                    print(f"🏗️  Đăng ký class: {cls['class_name']} ({cls['version']})")

                if callable(info.get("register")):
                    try:
                        info["register"](self)
                        print(f"✅ Plugin {filename} đã đăng ký thành công.")
                    except Exception as e:
                        print(f"⚠️ Lỗi khi gọi register() trong plugin {filename}: {e}")

    def process_input(self, user_input: str) -> bool:
        user_input = user_input.strip()
        for handler in self.handlers:
            if handler.can_handle(user_input):
                return handler.handle(user_input)
        print("🤷‍♂️ Tôi chưa hiểu yêu cầu của bạn.")
        return True

    def call_method(self, class_name: str, method_name: str, *args, version: Union[str, List[str]] = None, **kwargs):
        func = self.version_manager.get_method_version(class_name, method_name, version)
        if func:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"⚠️ Lỗi khi gọi {class_name}.{method_name}: {e}")
                return None
        print(f"⚠️ Không tìm thấy {class_name}.{method_name} ({version or self.version_manager.current_version})")
        return None

    def call_class_method(self, class_name: str, method_name: str, *args, version: str = None, **kwargs):
        cls = self.version_manager.get_class_version(class_name, version)
        if cls:
            try:
                instance = cls()
                method = getattr(instance, method_name)
                if callable(method):
                    return method(*args, **kwargs)
                else:
                    print(f"⚠️ {class_name}.{method_name} không phải là method.")
            except Exception as e:
                print(f"⚠️ Lỗi khi gọi {class_name}.{method_name}: {e}")
        else:
            print(f"⚠️ Không tìm thấy class {class_name} ({version or self.version_manager.current_version})")
        return None

    def run(self, mode: str = "manual", auto_file: str = None, auto_list: list = None, auto_generator: Any = None, delay: float = 0.0):
        def process_and_wait(command):
            print(f"\n❓ Auto: {command}")
            self.process_input(command)
            if delay > 0:
                time.sleep(delay)

        if mode == "auto_file":
            if not auto_file or not os.path.exists(auto_file):
                print(f"⚠️ Không tìm thấy file: {auto_file}")
                return
            with open(auto_file, "r", encoding="utf-8") as f:
                for line in f:
                    command = line.strip()
                    if not command:
                        continue
                    process_and_wait(command)
            print("✅ Hoàn thành auto_file run.")
            return

        elif mode == "auto_list":
            if not auto_list:
                print(f"⚠️ Danh sách lệnh trống.")
                return
            for command in auto_list:
                if not command.strip():
                    continue
                process_and_wait(command)
            print("✅ Hoàn thành auto_list run.")
            return

        elif mode == "auto_generator":
            if not auto_generator or not callable(auto_generator):
                print(f"⚠️ auto_generator cần là generator hoặc callable trả generator.")
                return
            gen = auto_generator() if callable(auto_generator) else auto_generator
            try:
                for command in gen:
                    if not command.strip():
                        continue
                    process_and_wait(command)
            except StopIteration:
                pass
            print("✅ Hoàn thành auto_generator run.")
            return

        # Mặc định: manual
        print("🤖 Trợ lý ảo sẵn sàng. Gõ 'thoát' để kết thúc.")
        while True:
            try:
                user_input = input("\n❓ Bạn hỏi gì?: ")
                if user_input.lower() in ["thoát", "exit", "quit"]:
                    print("👋 Tạm biệt!")
                    break
                self.process_input(user_input)
            except KeyboardInterrupt:
                print("\n👋 Tạm biệt!")
                break
            except Exception as e:
                print(f"⚠️ Lỗi: {e}")

# ==================== CHẠY ====================
if __name__ == "__main__":
    assistant = VirtualAssistantCore()
    assistant.run()
