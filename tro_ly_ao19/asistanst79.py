# class Loader dạng instance thay vì @staticmethod, @classmethod hỗ trợ kế thừa tốt hơn 
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

    def _ensure_version_exists(self, version: str) -> None:
        """Helper method to ensure version exists"""
        if version not in self.versions:
            self.versions[version] = {"methods": {}, "classes": {}, "description": ""}

    def register_method_version(self, class_name: str, method_name: str, version: str, method_ref: Callable, description: str = "", mode: str = "replace") -> bool:  
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

    def get_method_version(self, class_name: str, method_name: str, version: Union[str, List[str]] = None) -> Optional[Callable]:  
        versions = [version] if isinstance(version, str) else (version or [self.current_version])
        funcs = []

        for ver in versions:  
            method_info = self.versions.get(ver, {}).get("methods", {}).get(class_name, {}).get(method_name)
            if not method_info:
                continue
                
            func = method_info["function"]
            if isinstance(func, list):  
                funcs.extend((ver, f) for f in func)
            else:
                funcs.append((ver, func))

        if not funcs:  
            return None  

        return lambda *args, **kwargs: {ver: f(*args, **kwargs) for ver, f in funcs}

    def get_class_version(self, class_name: str, version: str = None) -> Optional[Any]:  
        version = version or self.current_version  
        return self.versions.get(version, {}).get("classes", {}).get(class_name)  

    def switch_version(self, version: str) -> bool:  
        if version in self.versions:  
            self.current_version = version  
            return True  
        return False

# ==================== LOADER CLASS ====================

class Loader:
    def __init__(self, base_folder: str = "."):
        self.base_folder = base_folder
        print(f"📦 Loader khởi tạo với thư mục gốc: {self.base_folder}")

    def ensure_folder(self, folder: str) -> None:
        path = os.path.join(self.base_folder, folder)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"✅ Đã tạo thư mục: {path}")

    def _load_classes_from_folder(
        self,
        folder: str,
        base_class: Optional[Type[T]] = None,
        info_attribute: Optional[str] = None,
        class_filter: Optional[Callable[[Type], bool]] = None,
        post_process: Optional[Callable[[Type], Any]] = None
    ) -> List[Type[T]]:
        self.ensure_folder(folder)
        classes = []
        path_folder = os.path.join(self.base_folder, folder)

        for filename in os.listdir(path_folder):
            if not filename.endswith(".py"):
                continue

            path = os.path.join(path_folder, filename)
            try:
                spec = importlib.util.spec_from_file_location("module", path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if info_attribute:
                    info = getattr(module, info_attribute, None)
                    if info and not info.get("enabled", True):
                        print(f"⏭️ Bỏ qua {filename} (disabled)")
                        continue

                for name in dir(module):
                    attr = getattr(module, name)
                    if isinstance(attr, type):
                        if base_class and not (issubclass(attr, base_class) and attr is not base_class):
                            continue
                        if class_filter and not class_filter(attr):
                            continue
                        result = post_process(attr) if post_process else attr
                        if result is not None:
                            classes.append(result)

            except Exception as e:
                print(f"❌ Lỗi nạp từ {filename}: {e}")

        return classes

    def load_version_manager(self) -> IVersionManager:
        print("🔍 Đang nạp VersionManager")
        implementations = self._load_classes_from_folder(
            "version_managers",
            base_class=IVersionManager,
            info_attribute="version_manager_info"
        )
        if implementations:
            manager = implementations[0]()
            print(f"✅ Sử dụng VersionManager: {type(manager).__name__}")
            return manager
        print("✅ Sử dụng BaseVersionManager mặc định.")
        return BaseVersionManager()

    def load_interfaces(self, interface_registry: Dict[str, Type]) -> None:
        print("🔍 Đang nạp Interfaces")
        def register_interface(cls: Type) -> None:
            interface_registry[cls.__name__] = cls
            print(f"🧩 Đăng ký Interface: {cls.__name__}")
            return None
        self._load_classes_from_folder("interfaces", post_process=register_interface)

    def load_plugins(self, assistant: Any) -> None:
        print("🔍 Đang nạp Plugins")
        self.ensure_folder("plugins")
        path_folder = os.path.join(self.base_folder, "plugins")

        for filename in os.listdir(path_folder):
            if not filename.endswith(".py"):
                continue

            path = os.path.join(path_folder, filename)
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

    def load_dynamic_assistants(self) -> None:
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

        self._load_classes_from_folder(
            "assistants",
            class_filter=lambda c: hasattr(c, "run") and callable(getattr(c, "run")),
            post_process=run_assistant
        )

    def load_run_mode(self, run_mode_name: str = None) -> Type:
        print("🔍 Đang nạp Run Modes")
        run_modes = self._load_classes_from_folder(
            "run",
            class_filter=lambda c: c.__name__.startswith("Run")
        )

        if not run_modes:
            return None
        if run_mode_name:
            for run_cls in run_modes:
                if getattr(run_cls, "name", "").lower() == run_mode_name.lower():
                    print(f"✅ Chạy chế độ run: {run_mode_name}")
                    return run_cls
            print(f"⚠️ Không tìm thấy Run mode '{run_mode_name}'")

        for run_cls in run_modes:
            if getattr(run_cls, "name", "").lower() == "interactive":
                print("✅ Dùng RunInteractive mặc định.")
                return run_cls

        return run_modes[0] if run_modes else None

    def load_process_input(self, assistant: 'VirtualAssistantCore') -> 'ProcessInput':
        print("🔍 Đang nạp Process Input Handlers")
        implementations = self._load_classes_from_folder(
            "process_inputs",
            base_class=ProcessInput,
            info_attribute="process_input_info"
        )
        if not implementations:
            print("✅ Sử dụng ProcessInput mặc định.")
            return ProcessInput(assistant)

        for impl in implementations:
            info = getattr(impl, "process_input_info", {})
            if info.get("preferred", False):
                print(f"✅ Sử dụng ProcessInput: {impl.__name__} (preferred)")
                return impl(assistant)

        print(f"✅ Sử dụng ProcessInput: {implementations[0].__name__}")
        return implementations[0](assistant)

    def load_command_handlers(self, assistant: 'VirtualAssistantCore') -> None:
        print("🔍 Đang nạp Command Handlers")
        handlers = self._load_classes_from_folder(
            "icommandhandlers",
            base_class=ICommandHandler
        )
        for handler_cls in handlers:
            try:
                instance = handler_cls()
                assistant.handlers.append(instance)
                print(f"✅ Đã đăng ký CommandHandler: {handler_cls.__name__}")
            except Exception as e:
                print(f"⚠️ Lỗi khi khởi tạo {handler_cls.__name__}: {e}")

    def load_loader_modules(self, assistant: 'VirtualAssistantCore') -> None:
        print("🔍 Đang nạp Loader Modules")
        self._load_classes_from_folder(
            "loader",
            post_process=lambda cls: print(f"✅ Tìm thấy Loader module: {cls.__name__}")
        )

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
        self.loader = Loader()
        self.version_manager = version_manager or self.loader.load_version_manager()
        self.handlers: List[ICommandHandler] = []  
        self.context: Dict[str, Any] = {}  
        self.interface_registry: Dict[str, Type] = {}  
        
        run_mode_class = self.loader.load_run_mode(run_mode_name)
        self.process_input = self.loader.load_process_input(self)
        self.runner = run_mode_class(self) if run_mode_class else Run(self)

        self.loader.load_interfaces(self.interface_registry)  
        self.loader.load_command_handlers(self)
        self.loader.load_plugins(self)
        self.loader.load_loader_modules(self)
    def call_method(self, class_name: str, method_name: str, *args, version: Union[str, List[str]] = None, **kwargs) -> Any:  
        func = self.version_manager.get_method_version(class_name, method_name, version)  
        if func:  
            try:  
                return func(*args, **kwargs)  
            except Exception as e:  
                print(f"⚠️ Lỗi khi gọi {class_name}.{method_name}: {e}")  
                return None  
        print(f"⚠️ Không tìm thấy {class_name}.{method_name} ({version or self.version_manager.current_version})")  
        return None  
    
    def call_class_method(self, class_name: str, method_name: str, *args, version: str = None, **kwargs) -> Any:  
        cls = self.version_manager.get_class_version(class_name, version)  
        if cls:  
            try:  
                instance = cls()  
                method = getattr(instance, method_name)  
                if callable(method):  
                    return method(*args, **kwargs)  
                print(f"⚠️ {class_name}.{method_name} không phải là method.")  
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
        self.loader = Loader()
        self._prepare_environment()
        core_impl = self._load_core_implementation()
        self.assistant = core_impl(version_manager, run_mode) if core_impl else VirtualAssistantCore(version_manager, run_mode)

    def _prepare_environment(self) -> None:
        for folder in ["version_managers", "interfaces", "plugins", "assistants", "virtualassistantcore", "process_inputs", "icommandhandlers", "loader"]:
            self.loader.ensure_folder(folder)

    def _load_core_implementation(self) -> Optional[Type[VirtualAssistantCore]]:
        cores = self.loader._load_classes_from_folder(
            "virtualassistantcore",
            base_class=VirtualAssistantCore,
            info_attribute="core_info"
        )
        if cores:
            print(f"✅ Sử dụng VirtualAssistantCore implement: {cores[0].__name__}")
            return cores[0]
        print("✅ Sử dụng VirtualAssistantCore mặc định.")
        return None

    def start(self) -> None:
        print("🚀 Đang khởi động Virtual Assistant...")
        try:
            self.assistant.run()
            self.loader.load_dynamic_assistants()
        except Exception as e:
            print(f"❌ Lỗi nghiêm trọng khi khởi động: {e}")
        finally:
            print("🛑 Hệ thống Virtual Assistant đã dừng")

# ==================== MAIN ====================

if __name__ == "__main__":
    assistant = StartVirtualAssistant(run_mode="interactive")
    assistant.start()