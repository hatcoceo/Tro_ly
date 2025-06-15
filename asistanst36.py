# core_assistant.py - Phần lõi của trợ lý ảo, điều phối, nạp plugin, quản lý method + class

import os
import importlib.util
from abc import ABC, abstractmethod
from typing import List, Tuple, Callable, Any, Optional

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
    def register_method_version(self, class_name: str, method_name: str, version: str, method_ref: Callable, description: str = "") -> bool:
        pass

    @abstractmethod
    def register_class_version(self, class_name: str, version: str, class_ref: Any) -> bool:
        pass

    @abstractmethod
    def get_method_version(self, class_name: str, method_name: str, version: str = None) -> Optional[Callable]:
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

    def register_method_version(self, class_name, method_name, version, method_ref, description=""):
        if version not in self.versions:
            self.versions[version] = {"methods": {}, "classes": {}, "description": ""}
        self.versions[version]["methods"].setdefault(class_name, {})[method_name] = {
            "function": method_ref,
            "description": description
        }
        return True

    def register_class_version(self, class_name, version, class_ref):
        if version not in self.versions:
            self.versions[version] = {"methods": {}, "classes": {}, "description": ""}
        self.versions[version]["classes"][class_name] = class_ref
        return True

    def get_method_version(self, class_name, method_name, version=None):
        version = version or self.current_version
        return self.versions.get(version, {}).get("methods", {}).get(class_name, {}).get(method_name, {}).get("function")

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
        self.context: dict = {}  # Dùng để chia sẻ giữa các plugin
        self.load_plugins("plugins")

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
                        method.get("description", "")
                    )
                    print(f"🧩 Đăng ký method: {method['class_name']}.{method['method_name']} ({method['version']})")

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

if __name__ == "__main__":
    assistant = VirtualAssistantCore()
    assistant.run()
