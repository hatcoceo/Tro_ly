# có thêm sử lý bất đồng bộ , đa luồng, đa tiến trình 
import os
import importlib.util
import time
import asyncio
import threading
import multiprocessing
from abc import ABC, abstractmethod
from typing import List, Callable, Any, Optional, Union
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from queue import Empty

# ==================== INTERFACES ====================

class ICommandHandler(ABC):
    @abstractmethod
    async def can_handle(self, command: str) -> bool:
        pass

    @abstractmethod
    async def handle(self, command: str) -> bool:
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
        self._lock = threading.Lock()

    def register_method_version(self, class_name, method_name, version, method_ref, description="", mode="replace"):
        with self._lock:
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
        with self._lock:
            if version not in self.versions:
                self.versions[version] = {"methods": {}, "classes": {}, "description": ""}
            self.versions[version]["classes"][class_name] = class_ref
            return True

    def get_method_version(self, class_name, method_name, version: Union[str, List[str]] = None):
        with self._lock:
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
        with self._lock:
            version = version or self.current_version
            return self.versions.get(version, {}).get("classes", {}).get(class_name)

    def switch_version(self, version):
        with self._lock:
            if version in self.versions:
                self.current_version = version
                return True
            return False

# ==================== WORKER FOR DISTRIBUTED PROCESSING ====================

class WorkerProcess:
    def __init__(self, task_queue: multiprocessing.Queue, result_queue: multiprocessing.Queue, version_manager: BaseVersionManager):
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.version_manager = version_manager

    def run(self):
        while True:
            try:
                task = self.task_queue.get(timeout=1)
                if task is None:
                    break
                class_name, method_name, args, kwargs, version = task
                result = self.execute_task(class_name, method_name, args, kwargs, version)
                self.result_queue.put(result)
            except Empty:
                continue
            except Exception as e:
                self.result_queue.put(f"Error: {e}")

    def execute_task(self, class_name, method_name, args, kwargs, version):
        func = self.version_manager.get_method_version(class_name, method_name, version)
        if func:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return f"Error executing {class_name}.{method_name}: {e}"
        return f"Method {class_name}.{method_name} not found for version {version}"

# ==================== CORE ASSISTANT ====================

class VirtualAssistantCore:
    def __init__(self, max_workers: int = 4):
        self.version_manager = BaseVersionManager()
        self.handlers: List[ICommandHandler] = []
        self.context: dict = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=max_workers)
        self.task_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        self.workers = [
            multiprocessing.Process(
                target=WorkerProcess(self.task_queue, self.result_queue, self.version_manager).run
            )
            for _ in range(max_workers)
        ]
        for worker in self.workers:
            worker.start()
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

    async def call_before_hooks(self, hook_name: str, *args, **kwargs):
        if self.hooks:
            await self.hooks.call_before_hooks(hook_name, *args, **kwargs)

    async def call_after_hooks(self, hook_name: str, result=None, *args, **kwargs):
        if self.hooks:
            await self.hooks.call_after_hooks(hook_name, result=result, *args, **kwargs)

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

    async def process_input(self, user_input: str) -> bool:
        user_input = user_input.strip()
        for handler in self.handlers:
            try:
                # Kiểm tra xem handler có hỗ trợ bất đồng bộ không
                can_handle = await handler.can_handle(user_input)
                if can_handle:
                    return await handler.handle(user_input)
            except Exception as e:
                print(f"⚠️ Lỗi khi xử lý handler cho lệnh '{user_input}': {e}")
        print("🤷‍♂️ Tôi chưa hiểu yêu cầu của bạn.")
        return True

    async def call_method(self, class_name: str, method_name: str, *args, version: Union[str, List[str]] = None, **kwargs):
        func = self.version_manager.get_method_version(class_name, method_name, version)
        if func:
            try:
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(self.executor, lambda: func(*args, **kwargs))
            except Exception as e:
                print(f"⚠️ Lỗi khi gọi {class_name}.{method_name}: {e}")
                return None
        print(f"⚠️ Không tìm thấy {class_name}.{method_name} ({version or self.version_manager.current_version})")
        return None

    async def call_class_method(self, class_name: str, method_name: str, *args, version: str = None, **kwargs):
        cls = self.version_manager.get_class_version(class_name, version)
        if cls:
            try:
                instance = cls()
                method = getattr(instance, method_name)
                if callable(method):
                    loop = asyncio.get_running_loop()
                    return await loop.run_in_executor(self.executor, lambda: method(*args, **kwargs))
                else:
                    print(f"⚠️ {class_name}.{method_name} không phải là method.")
            except Exception as e:
                print(f"⚠️ Lỗi khi gọi {class_name}.{method_name}: {e}")
        else:
            print(f"⚠️ Không tìm thấy class {class_name} ({version or self.version_manager.current_version})")
        return None

    def dispatch_distributed_task(self, class_name: str, method_name: str, *args, version: str = None, **kwargs):
        self.task_queue.put((class_name, method_name, args, kwargs, version))
        try:
            result = self.result_queue.get(timeout=5)
            return result
        except Empty:
            print(f"⚠️ Timeout khi chờ kết quả từ {class_name}.{method_name}")
            return None

    async def run(self, mode: str = "manual", auto_file: str = None, auto_list: list = None, auto_generator: Any = None, delay: float = 0.0):
        async def process_and_wait(command):
            print(f"\n❓ Auto: {command}")
            await self.process_input(command)
            if delay > 0:
                await asyncio.sleep(delay)

        if mode == "auto_file":
            if not auto_file or not os.path.exists(auto_file):
                print(f"⚠️ Không tìm thấy file: {auto_file}")
                return
            with open(auto_file, "r", encoding="utf-8") as f:
                tasks = [process_and_wait(line.strip()) for line in f if line.strip()]
                await asyncio.gather(*tasks)
            print("✅ Hoàn thành auto_file run.")
            return

        elif mode == "auto_list":
            if not auto_list:
                print(f"⚠️ Danh sách lệnh trống.")
                return
            tasks = [process_and_wait(command) for command in auto_list if command.strip()]
            await asyncio.gather(*tasks)
            print("✅ Hoàn thành auto_list run.")
            return

        elif mode == "auto_generator":
            if not auto_generator or not callable(auto_generator):
                print(f"⚠️ auto_generator cần là generator hoặc callable trả generator.")
                return
            gen = auto_generator() if callable(auto_generator) else auto_generator
            try:
                tasks = [process_and_wait(command) for command in gen if command.strip()]
                await asyncio.gather(*tasks)
            except StopIteration:
                pass
            print("✅ Hoàn thành auto_generator run.")
            return

        print("🤖 Trợ lý ảo sẵn sàng. Gõ 'thoát' để kết thúc.")
        while True:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(None, input, "\n❓ Bạn hỏi gì?: ")
                if user_input.lower() in ["thoát", "exit", "quit"]:
                    print("👋 Tạm biệt!")
                    break
                await self.process_input(user_input)
            except KeyboardInterrupt:
                print("\n👋 Tạm biệt!")
                break
            except Exception as e:
                print(f"⚠️ Lỗi: {e}")
        for _ in range(len(self.workers)):
            self.task_queue.put(None)
        for worker in self.workers:
            worker.join()

    def __del__(self):
        self.executor.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)

# ==================== CHẠY ====================
if __name__ == "__main__":
    assistant = VirtualAssistantCore(max_workers=4)
    asyncio.run(assistant.run())
