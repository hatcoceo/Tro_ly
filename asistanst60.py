import os
import importlib.util
from abc import ABC, abstractmethod
from typing import List, Callable, Any, Optional, Union, Type

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


# ==================== BASE VERSION MANAGER ====================

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
            methods[method_name] = {"function": method_ref, "description": description}
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
            methods[method_name] = {"function": current_func, "description": description}
        else:
            raise ValueError(f"Chế độ mode không hợp lệ: {mode}")

        return True

    def register_class_version(self, class_name, version, class_ref):
        if version not in self.versions:
            self.versions[version] = {"methods": {}, "classes": {}, "description": ""}
        self.versions[version]["classes"][class_name] = class_ref
        return True

    def get_method_version(self, class_name, method_name, version=None):
        version = version or self.current_version
        if isinstance(version, str):
            version = [version]

        funcs = []
        for ver in version:
            method_info = self.versions.get(ver, {}).get("methods", {}).get(class_name, {}).get(method_name)
            if method_info:
                func = method_info["function"]
                if isinstance(func, list):
                    for f in func:
                        funcs.append((ver, f))
                    continue
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


# ==================== LOADER CLASS ====================

class Loader:
    @staticmethod
    def ensure_folder(folder: str):
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"✅ Đã tạo thư mục: {folder}")

    @staticmethod
    def load_version_manager_implementations(folder: str) -> List[Type[IVersionManager]]:
        managers: List[Type[IVersionManager]] = []
        Loader.ensure_folder(folder)

        for filename in os.listdir(folder):
            if filename.endswith(".py"):
                path = os.path.join(folder, filename)
                try:
                    spec = importlib.util.spec_from_file_location("version_module", path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    for name in dir(module):
                        attr = getattr(module, name)
                        if isinstance(attr, type) and issubclass(attr, IVersionManager) and attr is not IVersionManager:
                            managers.append(attr)
                            print(f"🧩 Nạp VersionManager implement: {name} từ {filename}")
                except Exception as e:
                    print(f"❌ Lỗi nạp version manager từ {filename}: {e}")
        return managers

    @staticmethod
    def load_interfaces(folder: str, interface_registry: dict):
        Loader.ensure_folder(folder)
        for filename in os.listdir(folder):
            if filename.endswith(".py"):
                path = os.path.join(folder, filename)
                try:
                    spec = importlib.util.spec_from_file_location("interface_module", path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    for name in dir(module):
                        attr = getattr(module, name)
                        if isinstance(attr, type):
                            interface_registry[name] = attr
                            print(f"🧩 Đăng ký Interface: {name}")
                except Exception as e:
                    print(f"❌ Lỗi nạp interface {filename}: {e}")

    @staticmethod
    def load_plugins(folder: str, assistant: Any):
        Loader.ensure_folder(folder)
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

                register_func = info.get("register")
                if callable(register_func):
                    try:
                        register_func(assistant)
                        print(f"✅ Gọi plugin_info['register'] trong {filename}")
                    except Exception as e:
                        print(f"⚠️ Lỗi khi chạy plugin_info['register'] trong {filename}: {e}")

                for method in info.get("methods", []):
                    assistant.version_manager.register_method_version(
                        method["class_name"],
                        method["method_name"],
                        method["version"],
                        method["function"],
                        method.get("description", ""),
                        method.get("mode", "replace")
                    )
                    print(f"🧩 Đăng ký method: {method['class_name']}.{method['method_name']} ({method['version']})")

                for cls in info.get("classes", []):
                    assistant.version_manager.register_class_version(
                        cls["class_name"],
                        cls["version"],
                        cls["class_ref"]
                    )
                    print(f"🏗️  Đăng ký class: {cls['class_name']} ({cls['version']})")

    @staticmethod
    def load_dynamic_assistants(folder: str):
        Loader.ensure_folder(folder)

        for filename in os.listdir(folder):
            if filename.endswith(".py"):
                path = os.path.join(folder, filename)
                try:
                    spec = importlib.util.spec_from_file_location("assistant_module", path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    for name in dir(module):
                        attr = getattr(module, name)
                        if isinstance(attr, type):
                            if hasattr(attr, "run") and callable(getattr(attr, "run")):
                                try:
                                    instance = attr()
                                    print(f"🚀 Chạy assistant: {name} từ {filename}")
                                    instance.run()
                                except Exception as e:
                                    print(f"⚠️ Lỗi chạy {name} từ {filename}: {e}")

                except Exception as e:
                    print(f"❌ Lỗi import file {filename}: {e}")


# ==================== VIRTUAL ASSISTANT CORE ====================

class VirtualAssistantCore:
    def __init__(self, version_manager: Optional[IVersionManager] = None):
        Loader.ensure_folder("version_managers")
        Loader.ensure_folder("interfaces")
        Loader.ensure_folder("plugins")

        implementations = Loader.load_version_manager_implementations("version_managers")
        if implementations:
            self.version_manager = implementations[0]()
            print(f"✅ Sử dụng VersionManager: {type(self.version_manager).__name__}")
        else:
            self.version_manager = version_manager or BaseVersionManager()
            print(f"✅ Sử dụng BaseVersionManager mặc định.")

        self.handlers: List[ICommandHandler] = []
        self.context: dict = {}
        self.interface_registry = {}

        Loader.load_interfaces("interfaces", self.interface_registry)
        Loader.load_plugins("plugins", self)

    def run(self):
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

    def process_input(self, user_input: str) -> bool:
        user_input = user_input.strip()
        for handler in self.handlers:
            if handler.can_handle(user_input):
                return handler.handle(user_input)
        print("🤷‍♂️ Tôi chưa hiểu yêu cầu của bạn.")
        return True


# ==================== MAIN ====================

def start_virtual_assistant(assistant: VirtualAssistantCore):
    assistant.run()


if __name__ == "__main__":
    Loader.ensure_folder("assistants")

    assistant = VirtualAssistantCore()
    start_virtual_assistant(assistant)

    # Sau khi assistant core kết thúc, load thêm các assistants
    Loader.load_dynamic_assistants("assistants")