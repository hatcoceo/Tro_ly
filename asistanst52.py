import os
import importlib.util
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


# ==================== VIRTUAL ASSISTANT CORE ====================

class VirtualAssistantCore:
    def __init__(self, version_manager: Optional[IVersionManager] = None):
        self.version_manager = version_manager or BaseVersionManager()
        self.handlers: List[ICommandHandler] = []
        self.context: dict = {}
        self.interface_registry = {}

        self.load_interfaces("interfaces")
        self.load_plugins("plugins")

    def load_interfaces(self, folder: str):
        if not os.path.exists(folder):
            os.makedirs(folder)
            return

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
                            self.interface_registry[name] = attr
                            print(f"🧩 Đăng ký Interface: {name}")
                except Exception as e:
                    print(f"❌ Lỗi nạp interface {filename}: {e}")

    def load_plugins(self, folder: str):
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
                        method["class_name"],
                        method["method_name"],
                        method["version"],
                        method["function"],
                        method.get("description", ""),
                        method.get("mode", "replace")
                    )
                    print(f"🧩 Đăng ký method: {method['class_name']}.{method['method_name']} ({method['version']}, mode={method.get('mode', 'replace')})")

                for cls in info.get("classes", []):
                    self.version_manager.register_class_version(
                        cls["class_name"],
                        cls["version"],
                        cls["class_ref"]
                    )
                    print(f"🏗️  Đăng ký class: {cls['class_name']} ({cls['version']})")

                for iface in info.get("interfaces", []):
                    interface_name = iface["interface_name"]
                    methods = iface.get("methods", {})

                    interface_cls = self.interface_registry.get(interface_name)
                    if not interface_cls:
                        print(f"⚠️ Interface {interface_name} chưa được đăng ký.")
                        continue

                    class Impl(interface_cls):
                        pass

                    for method_name, func in methods.items():
                        setattr(Impl, method_name, staticmethod(func))

                    impl_list = self.interface_registry.setdefault("__impls__:" + interface_name, [])
                    impl_list.append(Impl())
                    print(f"✅ Plugin implement {interface_name}: {Impl}")

                if callable(info.get("register")):
                    try:
                        info["register"](self)
                        print(f"✅ Plugin {filename} đã đăng ký thành công.")
                    except Exception as e:
                        print(f"⚠️ Lỗi khi gọi register() trong plugin {filename}: {e}")

    def call_interface(self, interface_name: str, method_name: str, *args, **kwargs):
        impls = self.interface_registry.get("__impls__:" + interface_name, [])
        if not impls:
            print(f"⚠️ Chưa có implement nào cho interface {interface_name}.")
            return

        for impl in impls:
            method = getattr(impl, method_name, None)
            if callable(method):
                method(*args, **kwargs)

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


# ==================== NEW MAIN RUNNER ====================

def start_virtual_assistant(assistant: VirtualAssistantCore):
    """
    Hàm chạy VirtualAssistantCore.
    Có thể tái sử dụng ở nơi khác (ví dụ test, web, etc.)
    """
    assistant.run()


if __name__ == "__main__":
    assistant = VirtualAssistantCore()
    start_virtual_assistant(assistant)