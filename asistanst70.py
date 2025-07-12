import os
import importlib.util
from abc import ABC, abstractmethod
from typing import List, Callable, Any, Optional, Union, Type, Dict

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

    @staticmethod
    def load_version_managers(folder: str) -> List[Type[IVersionManager]]:
        version_managers: List[Type[IVersionManager]] = []
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
                            version_managers.append(attr)
                            print(f"🧩 Nạp VersionManager: {name} từ {filename}")
                except Exception as e:
                    print(f"❌ Lỗi nạp VersionManager từ {filename}: {e}")
        return version_managers

    @staticmethod
    def load_virtual_assistant_core_implementations(folder: str) -> List[Type['VirtualAssistantCore']]:
        cores: List[Type['VirtualAssistantCore']] = []
        Loader.ensure_folder(folder)

        for filename in os.listdir(folder):
            if filename.endswith(".py"):
                path = os.path.join(folder, filename)
                try:
                    spec = importlib.util.spec_from_file_location("core_module", path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    for name in dir(module):
                        attr = getattr(module, name)
                        if isinstance(attr, type) and issubclass(attr, VirtualAssistantCore) and attr is not VirtualAssistantCore:
                            cores.append(attr)
                            print(f"🧩 Nạp VirtualAssistantCore implement: {name} từ {filename}")
                except Exception as e:
                    print(f"❌ Lỗi nạp VirtualAssistantCore từ {filename}: {e}")
        return cores

# ==================== PROCESS INPUT CLASS ====================

class ProcessInput:
    def __init__(self, assistant: 'VirtualAssistantCore'):
        self.assistant = assistant
        self.exit_commands = ["thoát", "exit", "quit"]

    def is_exit_command(self, user_input: str) -> bool:
        """Check if the user input is an exit command"""
        return user_input.lower().strip() in self.exit_commands

    def process(self, user_input: str) -> bool:
        """Process user input and return whether to continue running"""
        user_input = user_input.strip()
        
        if self.is_exit_command(user_input):
            print("👋 Tạm biệt!")
            return False

        for handler in self.assistant.handlers:
            if handler.can_handle(user_input):
                return handler.handle(user_input)
                
        print("🤷‍♂️ Tôi chưa hiểu yêu cầu của bạn.")
        return True

# ==================== RUN CLASS ====================

class Run:
    def __init__(self, assistant: 'VirtualAssistantCore'):
        self.assistant = assistant
        self.process_input = ProcessInput(assistant)
        self.running = False

    def start(self):
        """Start the main execution loop of the assistant"""
        self.running = True
        print("🤖 Trợ lý ảo sẵn sàng. Gõ 'thoát' để kết thúc.")
        
        while self.running:
            try:
                user_input = input("\n❓ Bạn hỏi gì?: ")
                self.running = self.process_input.process(user_input)
            except KeyboardInterrupt:
                print("\n👋 Tạm biệt!")
                self.running = False
            except Exception as e:
                print(f"⚠️ Lỗi: {e}")
                self.running = False

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
        self.runner = Run(self)

        Loader.load_interfaces("interfaces", self.interface_registry)  
        Loader.load_plugins("plugins", self)
    
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
        """Start the assistant"""
        self.runner.start()

# ==================== START VIRTUAL ASSISTANT CLASS ====================

class StartVirtualAssistant:
    """
    Class để khởi động và quản lý Virtual Assistant với các tính năng:
    - Tự động tạo thư mục cần thiết
    - Load các thành phần (version managers, interfaces, plugins)
    - Chạy các dynamic assistants
    - Cung cấp interface đơn giản để khởi động hệ thống
    """
    
    def __init__(self, version_manager: Optional[IVersionManager] = None):
        """
        Khởi tạo Virtual Assistant với VersionManager tùy chọn
        Nếu không cung cấp sẽ sử dụng BaseVersionManager mặc định
        """
        # Bước 1: load version managers
        Loader.ensure_folder("version_managers")
        version_managers = Loader.load_version_managers("version_managers")

        version_manager = None
        if version_managers:
            version_manager_cls = version_managers[0]
            version_manager = version_manager_cls()
            print(f"✅ Sử dụng VersionManager: {version_manager_cls.__name__}")
        else:
            print("⚠️ Không tìm thấy VersionManager. Sẽ tiếp tục mà không có version manager.")

        # Bước 2: load virtual assistant core implementations
        Loader.ensure_folder("virtualassistantcore")
        cores = Loader.load_virtual_assistant_core_implementations("virtualassistantcore")

        if cores:
            core_cls = cores[0]
            self.assistant = core_cls(version_manager)
            print(f"✅ Sử dụng VirtualAssistantCore implement: {core_cls.__name__}")
        else:
            self.assistant = VirtualAssistantCore(version_manager)
            print(f"✅ Sử dụng VirtualAssistantCore mặc định.")
            
        self._prepare_environment()
    
    def _prepare_environment(self):
        """Chuẩn bị môi trường bằng cách tạo các thư mục cần thiết"""
        required_folders = [
            "version_managers",
            "interfaces", 
            "plugins",
            "assistants",
            "virtualassistantcore"
        ]
        
        for folder in required_folders:
            Loader.ensure_folder(folder)
    
    def start(self):
        """
        Khởi động hệ thống Virtual Assistant
        - Chạy main assistant
        - Load các dynamic assistants
        """
        print("🚀 Đang khởi động Virtual Assistant...")
        try:
            # Chạy main assistant
            self.assistant.run()
            
            # Load và chạy các dynamic assistants
            Loader.load_dynamic_assistants("assistants")
            
        except Exception as e:
            print(f"❌ Lỗi nghiêm trọng khi khởi động: {e}")
        finally:
            print("🛑 Hệ thống Virtual Assistant đã dừng")

# ==================== MAIN ====================

if __name__ == "__main__":
    # Khởi tạo và chạy Virtual Assistant
    assistant = StartVirtualAssistant()
    assistant.start()