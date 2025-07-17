# dùng cú pháp rút gọn mã hơn asistanst76
import os
import importlib.util
from abc import ABC, abstractmethod
from typing import List, Callable, Any, Optional, Union, Type, Dict, TypeVar

T = TypeVar('T')

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
    def register_method_version(self, class_name: str, method_name: str, version: str, 
                             method_ref: Callable, description: str = "", mode: str = "replace") -> bool:
        pass

    @abstractmethod  
    def register_class_version(self, class_name: str, version: str, class_ref: Any) -> bool:  
        pass  

    @abstractmethod  
    def get_method_version(self, class_name: str, method_name: str, 
                         version: Union[str, List[str]] = None) -> Optional[Callable]:  
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

    def _ensure_version_exists(self, version: str) -> None:
        """Helper method to ensure version exists"""
        if version not in self.versions:
            self.versions[version] = {"methods": {}, "classes": {}, "description": ""}

    def register_method_version(self, class_name: str, method_name: str, version: str, 
                              method_ref: Callable, description: str = "", mode: str = "replace") -> bool:  
        self._ensure_version_exists(version)
        methods = self.versions[version]["methods"].setdefault(class_name, {})
        
        if mode == "replace" or method_name not in methods:  
            methods[method_name] = {"function": method_ref, "description": description}  
            return True
            
        if mode == "append":  
            old_func = methods[method_name]["function"]  
            methods[method_name] = {  
                "function": lambda *args, **kwargs: (old_func(*args, **kwargs), method_ref(*args, **kwargs)),
                "description": f"{methods[method_name]['description']} + {description}"
            }  
            return True
            
        if mode == "multi":  
            current_func = methods.get(method_name, {}).get("function")  
            funcs = [current_func] if current_func and not isinstance(current_func, list) else (current_func or [])
            funcs.append(method_ref)
            methods[method_name] = {"function": funcs, "description": description}
            return True
            
        raise ValueError(f"Chế độ mode không hợp lệ: {mode}")

    def register_class_version(self, class_name: str, version: str, class_ref: Any) -> bool:  
        self._ensure_version_exists(version)
        self.versions[version]["classes"][class_name] = class_ref  
        return True  

    def get_method_version(self, class_name: str, method_name: str, 
                         version: Union[str, List[str]] = None) -> Optional[Callable]:  
        versions = [version] if isinstance(version, str) else (version or [self.current_version])
        funcs = [(ver, f) for ver in versions  
                for f in (self.versions.get(ver, {}).get("methods", {}).get(class_name, {}).get(method_name, {}).get("function") or [])
                if f]

        return lambda *args, **kwargs: {ver: f(*args, **kwargs) for ver, f in funcs} if funcs else None

    def get_class_version(self, class_name: str, version: str = None) -> Optional[Any]:  
        return self.versions.get(version or self.current_version, {}).get("classes", {}).get(class_name)  

    def switch_version(self, version: str) -> bool:  
        if version in self.versions:  
            self.current_version = version  
            return True  
        return False

# ==================== LOADER CLASS ====================

class Loader:
    @staticmethod
    def ensure_folder(folder: str) -> None:
        """Ensure the specified folder exists, create if it doesn't"""
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"✅ Đã tạo thư mục: {folder}")

    @staticmethod
    def _load_classes_from_folder(
        folder: str,
        base_class: Optional[Type[T]] = None,
        info_attribute: Optional[str] = None,
        class_filter: Optional[Callable[[Type], bool]] = None,
        post_process: Optional[Callable[[Type], Any]] = None
    ) -> List[Type[T]]:
        """Base method for loading classes from Python files in a folder"""
        Loader.ensure_folder(folder)
        classes = []

        for filename in os.listdir(folder):
            if not filename.endswith(".py"):
                continue

            path = os.path.join(folder, filename)
            try:
                spec = importlib.util.spec_from_file_location("module", path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if info_attribute and getattr(module, info_attribute, {}).get("enabled", True) is False:
                    print(f"⏭️ Bỏ qua {filename} (disabled)")
                    continue

                for name in dir(module):
                    attr = getattr(module, name)
                    if isinstance(attr, type):
                        if (not base_class or (issubclass(attr, base_class) and attr is not base_class)) and (
                            not class_filter or class_filter(attr)):
                            
                            if post_process:
                                result = post_process(attr)
                                if result is not None:
                                    classes.append(result)
                            else:
                                classes.append(attr)

            except Exception as e:
                print(f"❌ Lỗi nạp từ {filename}: {e}")

        return classes

    @classmethod
    def load_version_manager(cls) -> IVersionManager:
        """Factory method to create appropriate version manager"""
        print("🔍 Đang nạp VersionManager")
        implementations = cls._load_classes_from_folder(
            "version_managers",
            base_class=IVersionManager,
            info_attribute="version_manager_info"
        )
        
        return implementations[0]() if implementations else (
            print("✅ Sử dụng BaseVersionManager mặc định.") or BaseVersionManager())

    @classmethod  
    def load_interfaces(cls, interface_registry: Dict[str, Type]) -> None:  
        """Load interfaces and register them in the provided registry"""
        print("🔍 Đang nạp Interfaces")
        
        def register_interface(cls: Type) -> None:
            interface_registry[cls.__name__] = cls
            print(f"🧩 Đăng ký Interface: {cls.__name__}")
            return None

        cls._load_classes_from_folder(
            "interfaces",
            post_process=register_interface
        )

    @classmethod  
    def load_plugins(cls, assistant: Any) -> None:  
        """Load and register plugins with the assistant"""
        print("🔍 Đang nạp Plugins")
        cls.ensure_folder("plugins")
        
        for filename in os.listdir("plugins"):
            if not filename.endswith(".py"):
                continue

            path = os.path.join("plugins", filename)
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

            if callable(info.get("register")):
                try:
                    info["register"](assistant)
                    print(f"✅ Gọi plugin_info['register'] trong {filename}")
                except Exception as e:
                    print(f"⚠️ Lỗi khi chạy plugin_info['register'] trong {filename}: {e}")

            for method in info.get("methods", []):
                assistant.version_manager.register_method_version(**method)
                print(f"🧩 Đăng ký method: {method['class_name']}.{method['method_name']} ({method['version']})")

            for cls in info.get("classes", []):
                assistant.version_manager.register_class_version(**cls)
                print(f"🏗️  Đăng ký class: {cls['class_name']} ({cls['version']})")

    @classmethod  
    def load_dynamic_assistants(cls) -> None:  
        """Load and run dynamic assistants"""
        print("🔍 Đang nạp Dynamic Assistants")
        
        def run_assistant(cls: Type) -> None:
            if hasattr(cls, "run") and callable(getattr(cls, "run")):
                try:
                    instance = cls()
                    print(f"🚀 Chạy assistant: {cls.__name__}")
                    instance.run()
                except Exception as e:
                    print(f"⚠️ Lỗi chạy {cls.__name__}: {e}")
            return None

        cls._load_classes_from_folder(
            "assistants",
            class_filter=lambda c: hasattr(c, "run") and callable(getattr(c, "run")),
            post_process=run_assistant
        )

    @classmethod
    def load_run_mode(cls, run_mode_name: str = None) -> Type:
        """Load and select appropriate run mode"""
        print("🔍 Đang nạp Run Modes")
        
        run_modes = cls._load_classes_from_folder(
            "run",
            class_filter=lambda c: c.__name__.startswith("Run")
        )
        
        if run_mode_name:
            for run_cls in run_modes:
                if getattr(run_cls, "name", "").lower() == run_mode_name.lower():
                    print(f"✅ Chạy chế độ run: {run_mode_name}")
                    return run_cls
            print(f"⚠️ Không tìm thấy Run mode '{run_mode_name}'")
        
        # Fallback to Interactive or first available
        return next((c for c in run_modes if getattr(c, "name", "").lower() == "interactive"), 
               run_modes[0] if run_modes else None)

    @classmethod
    def load_process_input(cls, assistant: 'VirtualAssistantCore') -> 'ProcessInput':
        """Load and select appropriate process input handler"""
        print("🔍 Đang nạp Process Input Handlers")
        
        implementations = cls._load_classes_from_folder(
            "process_inputs",
            base_class=ProcessInput,
            info_attribute="process_input_info"
        )
        
        preferred = next((i for i in implementations if getattr(i, "process_input_info", {}).get("preferred", False)), None)
        print(f"✅ Sử dụng ProcessInput: {preferred.__name__ if preferred else 'ProcessInput mặc định'}")
        return (preferred or ProcessInput)(assistant)

# ==================== BASE PROCESS INPUT CLASS ====================

class ProcessInput:
    def __init__(self, assistant: 'VirtualAssistantCore'):
        self.assistant = assistant
        self.exit_commands = ["thoát", "exit", "quit"]

    def is_exit_command(self, user_input: str) -> bool:
        return user_input.lower().strip() in self.exit_commands

    def process(self, user_input: str) -> bool:
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
        self.running = False

    def start(self) -> None:
        self.running = True
        print("🤖 Trợ lý ảo sẵn sàng. Gõ 'thoát' để kết thúc.")
        
        while self.running:
            try:
                user_input = input("\n❓ Bạn hỏi gì?: ")
                self.running = self.assistant.process_input.process(user_input)
            except KeyboardInterrupt:
                print("\n👋 Tạm biệt!")
                self.running = False
            except Exception as e:
                print(f"⚠️ Lỗi: {e}")
                self.running = False

# ==================== VIRTUAL ASSISTANT CORE ====================

class VirtualAssistantCore:
    def __init__(self, version_manager: Optional[IVersionManager] = None, run_mode_name: str = None):
        self.version_manager = version_manager or Loader.load_version_manager()
        self.handlers: List[ICommandHandler] = []  
        self.context: Dict[str, Any] = {}  
        self.interface_registry: Dict[str, Type] = {}  
        
        self.runner = (Loader.load_run_mode(run_mode_name) or Run)(self)
        self.process_input = Loader.load_process_input(self)

        Loader.load_interfaces(self.interface_registry)  
        Loader.load_plugins(self)

    def call_method(self, class_name: str, method_name: str, *args, 
                   version: Union[str, List[str]] = None, **kwargs) -> Any:  
        if func := self.version_manager.get_method_version(class_name, method_name, version):  
            try:  
                return func(*args, **kwargs)  
            except Exception as e:  
                print(f"⚠️ Lỗi khi gọi {class_name}.{method_name}: {e}")  
                return None  
        print(f"⚠️ Không tìm thấy {class_name}.{method_name} ({version or self.version_manager.current_version})")  
        return None  
    
    def call_class_method(self, class_name: str, method_name: str, *args, 
                         version: str = None, **kwargs) -> Any:  
        if cls := self.version_manager.get_class_version(class_name, version):  
            try:  
                instance = cls()  
                method = getattr(instance, method_name)  
                return method(*args, **kwargs) if callable(method) else print(f"⚠️ {class_name}.{method_name} không phải là method.")  
            except Exception as e:  
                print(f"⚠️ Lỗi khi gọi {class_name}.{method_name}: {e}")  
        else:  
            print(f"⚠️ Không tìm thấy class {class_name} ({version or self.version_manager.current_version})")  
        return None  
    
    def run(self) -> None:  
        self.runner.start()

# ==================== START VIRTUAL ASSISTANT CLASS ====================

class StartVirtualAssistant:
    def __init__(self, version_manager: Optional[IVersionManager] = None, run_mode: str = None):
        self._prepare_environment()
        
        # Load core implementation if available
        core_impl = next(iter(Loader._load_classes_from_folder(
            "virtualassistantcore",
            base_class=VirtualAssistantCore,
            info_attribute="core_info"
        )), None)
        
        print(f"✅ Sử dụng VirtualAssistantCore implement: {core_impl.__name__}" if core_impl else "✅ Sử dụng VirtualAssistantCore mặc định.")
        self.assistant = (core_impl or VirtualAssistantCore)(version_manager, run_mode)
    
    def _prepare_environment(self) -> None:
        """Chuẩn bị môi trường bằng cách tạo các thư mục cần thiết"""
        [Loader.ensure_folder(f) for f in ["version_managers", "interfaces", "plugins", "assistants", "virtualassistantcore", "process_inputs"]]
    
    def start(self) -> None:
        print("🚀 Đang khởi động Virtual Assistant...")
        try:
            self.assistant.run()
            Loader.load_dynamic_assistants()
        except Exception as e:
            print(f"❌ Lỗi nghiêm trọng khi khởi động: {e}")
        finally:
            print("🛑 Hệ thống Virtual Assistant đã dừng")

# ==================== MAIN ====================

if __name__ == "__main__":
    StartVirtualAssistant(run_mode="interactive").start()