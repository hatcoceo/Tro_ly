# assistant 43 - Enhanced with async, threading, multiprocessing, and distributed processing
import os
import importlib.util
import time
import asyncio
import threading
import multiprocessing
import logging
import pika
from abc import ABC, abstractmethod
from typing import List, Callable, Any, Optional, Union, Dict, Awaitable
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import wraps
import aiofiles
import json

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - (%(threadName)s)",
)
logger = logging.getLogger(__name__)

# ==================== INTERFACES ====================

class ICommandHandler(ABC):
    @abstractmethod
    async def can_handle(self, command: str) -> bool:
        pass

    @abstractmethod
    async def handle(self, command: str)
-> bool:
        pass

class IVersionManager(ABC
    @abstractmethod
    def register_method_version(
        self, class_name: str,
        method_name: str, version: str,
        method_ref: Union[Callable, Awaitable],
        description: str = "",
        mode: str = "replace",
    ) -> bool:
        pass

    @abstractmethod
    async def register_class_version(self, class_name: str,
        version: str, class_ref: Any) -> bool:
        pass

    @abstractmethod
    async def get_method_version(
        self, class_name: str,
        method_name: str,
        version: Union[str, List[str]] = None,
    ) -> Optional[Union[Callable, Awaitable]]:
        pass

    @abstractmethod
    async def get_class_version(
        self, class_name: str, version: str = None
    ) -> Optional[Any]:
        pass

    @abstractmethod
    async def switch_version(self, version: str) -> bool:
        pass

# ==================== VERSION MANAGER ====================

class BaseVersionManager(IVersionManager):
    def __init__(self):
        self._lock = asyncio.Lock()  # Lock cho bất đồng bộ
        self.versions = {
            "default": {
                "methods": {},
                "classes": {},
                "description": "Mặc định",
            }
        }
        self.current_version = "default"
        self._thread_pool = ThreadPoolExecutor(max_workers=4)
        self._process_pool = ProcessPoolExecutor(max_workers=2)

    async def register_method_version(
        self,
        class_name: str,
        method_name: str,
        version: str,
        method_ref: Union[Callable, Awaitable],
        description: str = "",
        mode: str = "replace",
    ):
        async with self._lock:
            if version not in self.versions:
                self.versions[version] = {
                    "methods": {},
                    "classes": {},
                    "description": "",
                }
            methods = self.versions[version]["methods"].setdefault(class_name, {})

            if mode == "replace" or method_name not in methods:
                methods[method_name] = {
                    "function": method_ref,
                    "description": description,
                }

            elif mode == "append":
                old_func = methods[method_name]["function"]

                @wraps(old_func)
                async def combined_func(*args, **kwargs):
                    old_result = (
                        await old_func(*args, **kwargs)
                        if asyncio.iscoroutinefunction(old_func)
                        else old_func(*args, **kwargs)
                    )
                    new_result = (
                        await method_ref(*args, **kwargs)
                        if asyncio.iscoroutinefunction(method_ref)
                        else method_ref(*args, **kwargs)
                    )
                    return (old_result, new_result)

                methods[method_name] = {
                    "function": combined_func,
                    "description": methods[method_name]["description"]
                    + " + "
                    + description,
                }

            elif mode == "multi":
                current_func = methods.get(method_name, {}).get("function")
                if not isinstance(current_func, list):
                    current_func = [current_func] if current_func else []
                current_func.append(method_ref)
                methods[method_name] = {
                    "function": current_func,
                    "description": description,
                }

            else:
                raise ValueError(f"Chế độ mode không hợp lệ: {mode}")

            logger.info(
                f"Đăng ký method: {class_name}.{method_name} (version={version}, mode={mode})"
            )
            return True

    async def register_class_version(self, class_name: str, version: str, class_ref: Any):
        async with self._lock:
            if version not in self.versions:
                self.versions[version] = {
                    "methods": {},
                    "classes": {},
                    "description": "",
                }
            self.versions[version]["classes"][class_name] = class_ref
            logger.info(f"Đăng ký class: {class_name} (version={version})")
            return True

    async def get_method_version(
        self,
        class_name: str,
        method_name: str,
        version: Union[str, List[str]] = None,
    ):
        async with self._lock:
            version = version or self.current_version
            if isinstance(version, str):
                version = [version]

            funcs = []
            for ver in version:
                method_info = (
                    self.versions.get(ver, {})
                    .get("methods", {})
                    .get(class_name, {})
                    .get(method_name)
                )
                if method_info:
                    func = method_info["function"]
                    if isinstance(func, list):
                        funcs.extend([(ver, f) for f in func])
                    else:
                        funcs.append((ver, func))

            if not funcs:
                return None

            async def combined(*args, **kwargs):
                results = {}
                for ver, f in funcs:
                    if asyncio.iscoroutinefunction(f):
                        results[ver] = await f(*args, **kwargs)
                    else:
                        # Chạy hàm đồng bộ trong thread pool
                        results[ver] = await asyncio.get_event_loop().run_in_executor(
                            self._thread_pool, lambda: f(*args, **kwargs)
                        )
                return results

            return combined

    async def get_class_version(self, class_name: str, version: str = None):
        async with self._lock:
            version = version or self.current_version
            return self.versions.get(version, {}).get("classes", {}).get(class_name)

    async def switch_version(self, version: str):
        async with self._lock:
            if version in self.versions:
                self.current_version = version
                logger.info(f"Chuyển sang version: {version}")
                return True
            logger.warning(f"Version không tồn tại: {version}")
            return False

    def __del__(self):
        self._thread_pool.shutdown()
        self._process_pool.shutdown()

# ==================== MESSAGE QUEUE FOR DISTRIBUTED PROCESSING ====================

class RabbitMQClient:
    def __init__(self, host: str = "localhost", queue: str = "assistant_tasks"):
        self.host = host
        self.queue = queue
        self.connection = None
        self.channel = None

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host)
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue, durable=True)
            logger.info(f"Kết nối RabbitMQ thành công: {self.host}")
        except Exception as e:
            logger.error(f"Lỗi kết nối RabbitMQ: {e}")

    def publish_task(self, task: Dict):
        if self.channel:
            self.channel.basic_publish(
                exchange="",
                routing_key=self.queue,
                body=json.dumps(task),
                properties=pika.BasicProperties(delivery_mode=2),  # Persistent
            )
            logger.info(f"Gửi task tới queue: {task}")

    def consume_tasks(self, callback):
        if self.channel:
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=self.queue, on_message_callback=callback, auto_ack=False
            )
            logger.info(f"Bắt đầu tiêu thụ tasks từ queue: {self.queue}")
            self.channel.start_consuming()

    def close(self):
        if self.connection:
            self.connection.close()
            logger.info("Đóng kết nối RabbitMQ")

# ==================== CORE ASSISTANT ====================

class VirtualAssistantCore:
    def __init__(self):
        self.version_manager = BaseVersionManager()
        self.handlers: List[ICommandHandler] = []
        self.context: Dict = {}
        self._lock = asyncio.Lock()
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._process_executor = ProcessPoolExecutor(max_workers=2)
        self._mq_client = RabbitMQClient()
        self._loop = asyncio.get_event_loop()
        self._running = True

        # Kết nối RabbitMQ trong luồng riêng
        threading.Thread(
            target=self._mq_client.connect, daemon=True, name="RabbitMQ-Connect"
        ).start()

        # Tải plugins bất đồng bộ
        asyncio.create_task(self.load_plugins("plugins"))

    @property
    def shared_registry(self):
        return self.context.get("shared_registry")

    @property
    def hooks(self):
        return self.context.get("hook_manager")

    def register_before_hook(self, hook_name: str, handler: Union[Callable, Awaitable]):
        if self.hooks:
            self.hooks.register_before_hook(hook_name, handler)

    def register_after_hook(self, hook_name: str, handler: Union[Callable, Awaitable]):
        if self.hooks:
            self.hooks.register_after_hook(hook_name, handler)

    async def call_before_hooks(self, hook_name: str, *args, **kwargs):
        if self.hooks:
            await self.hooks.call_before_hooks(hook_name, *args, **kwargs)

    async def call_after_hooks(self, hook_name: str, result=None, *args, **kwargs):
        if self.hooks:
            await self.hooks.call_after_hooks(hook_name, result=result, *args, **kwargs)

    async def load_plugins(self, folder: str):
        async with self._lock:
            if not os.path.exists(folder):
                os.makedirs(folder)
                return

            async def load_single_plugin(filename):
                path = os.path.join(folder, filename)
                try:
                    spec = importlib.util.spec_from_file_location("plugin_module", path)
                    plugin = importlib.util.module_from_spec(spec)
                    await self._loop.run_in_executor(
                        self._executor, spec.loader.exec_module, plugin
                    )
                except Exception as e:
                    logger.error(f"Lỗi plugin {filename}: {e}")
                    return

                info = getattr(plugin, "plugin_info", None)
                if not info or not info.get("enabled", True):
                    return

                for method in info.get("methods", []):
                    await self.version_manager.register_method_version(
                        method["class_name"],
                        method["method_name"],
                        method["version"],
                        method["function"],
                        method.get("description", ""),
                        method.get("mode", "replace"),
                    )

                for cls in info.get("classes", []):
                    await self.version_manager.register_class_version(
                        cls["class_name"], cls["version"], cls["class_ref"]
                    )

                if callable(info.get("register")):
                    try:
                        await self._loop.run_in_executor(
                            self._executor, info["register"], self
                        )
                        logger.info(f"Plugin {filename} đăng ký thành công.")
                    except Exception as e:
                        logger.error(f"Lỗi khi gọi register() trong plugin {filename}: {e}")

            tasks = []
            for filename in os.listdir(folder):
                if filename.endswith(".py"):
                    tasks.append(load_single_plugin(filename))
            await asyncio.gather(*tasks, return_exceptions=True)

    async def process_input(self, user_input: str) -> bool:
        user_input = user_input.strip()
        async with self._lock:
            for handler in self.handlers:
                if await handler.can_handle(user_input):
                    return await handler.handle(user_input)
        logger.warning(f"Yêu cầu không được xử lý: {user_input}")
        print("🤷‍♂️ Tôi chưa hiểu yêu cầu của bạn.")
        return True

    async def call_method(
        self,
        class_name: str,
        method_name: str,
        *args,
        version: Union[str, List[str]] = None,
        **kwargs,
    ):
        func = await self.version_manager.get_method_version(class_name, method_name, version)
        if func:
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return await self._loop.run_in_executor(
                        self._executor, lambda: func(*args, **kwargs)
                    )
            except Exception as e:
                logger.error(f"Lỗi khi gọi {class_name}.{method_name}: {e}")
                return None
        logger.warning(
            f"Không tìm thấy {class_name}.{method_name} (version={version or self.version_manager.current_version})"
        )
        return None

    async def call_class_method(
        self,
        class_name: str,
        method_name: str,
        *args,
        version: str = None,
        **kwargs,
    ):
        cls = await self.version_manager.get_class_version(class_name, version)
        if cls:
            try:
                instance = cls()
                method = getattr(instance, method_name)
                if callable(method):
                    if asyncio.iscoroutinefunction(method):
                        return await method(*args, **kwargs)
                    else:
                        return await self._loop.run_in_executor(
                            self._executor, lambda: method(*args, **kwargs)
                        )
                else:
                    logger.warning(f"{class_name}.{method_name} không phải là method.")
            except Exception as e:
                logger.error(f"Lỗi khi gọi {class_name}.{method_name}: {e}")
        else:
            logger.warning(
                f"Không tìm thấy class {class_name} (version={version or self.version_manager.current_version})"
            )
        return None

    def _process_task_in_process(self, task: Dict):
        # Hàm này chạy trong tiến trình riêng
        async def process():
            assistant = VirtualAssistantCore()
            await assistant.process_input(task["command"])
            return {"status": "completed", "command": task["command"]}

        return asyncio.run(process())

    def _rabbitmq_callback(self, ch, method, properties, body):
        try:
            task = json.loads(body)
            logger.info(f"Nhận task từ RabbitMQ: {task}")
            # Chạy task trong process pool
            future = self._process_executor.submit(self._process_task_in_process, task)
            result = future.result()
            logger.info(f"Kết quả task: {result}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Lỗi xử lý task RabbitMQ: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    async def run(
        self,
        mode: str = "manual",
        auto_file: str = None,
        auto_list: List[str] = None,
        auto_generator: Any = None,
        delay: float = 0.0,
    ):
        async def process_and_wait(command):
            print(f"\n❓ Auto: {command}")
            # Gửi task tới RabbitMQ thay vì xử lý trực tiếp
            self._mq_client.publish_task({"command": command})
            if delay > 0:
                await asyncio.sleep(delay)

        # Khởi động consumer RabbitMQ trong luồng riêng
        threading.Thread(
            target=self._mq_client.consume_tasks,
            args=(self._rabbitmq_callback,),
            daemon=True,
            name="RabbitMQ-Consumer",
        ).start()

        if mode == "auto_file":
            if not auto_file or not os.path.exists(auto_file):
                logger.error(f"Không tìm thấy file: {auto_file}")
                return
            async with aiofiles.open(auto_file, "r", encoding="utf-8") as f:
                async for line in f:
                    command = line.strip()
                    if not command:
                        continue
                    await process_and_wait(command)
            logger.info("Hoàn thành auto_file run.")
            return

        elif mode == "auto_list":
            if not auto_list:
                logger.error("Danh sách lệnh trống.")
                return
            for command in auto_list:
                if not command.strip():
                    continue
                await process_and_wait(command)
            logger.info("Hoàn thành auto_list run.")
            return

        elif mode == "auto_generator":
            if not auto_generator or not callable(auto_generator):
                logger.error("auto_generator cần là generator hoặc callable trả generator.")
                return
            gen = auto_generator() if callable(auto_generator) else auto_generator
            try:
                for command in gen:
                    if not command.strip():
                        continue
                    await process_and_wait(command)
            except StopIteration:
                pass
            logger.info("Hoàn thành auto_generator run.")
            return

        # Manual mode
        print("🤖 Trợ lý ảo sẵn sàng. Gõ 'thoát' để kết thúc.")
        while self._running:
            try:
                user_input = await self._loop.run_in_executor(
                    self._executor, input, "\n❓ Bạn hỏi gì?: "
                )
                if user_input.lower() in ["thoát", "exit", "quit"]:
                    print("👋 Tạm biệt!")
                    break
                await self.process_input(user_input)
            except KeyboardInterrupt:
                print("\n👋 Tạm biệt!")
                break
            except Exception as e:
                logger.error(f"Lỗi: {e}")

    def stop(self):
        self._running = False
        self._mq_client.close()
        self._executor.shutdown()
        self._process_executor.shutdown()

# ==================== CHẠY ====================

if __name__ == "__main__":
    async def main():
        assistant = VirtualAssistantCore()
        try:
            await assistant.run()
        finally:
            assistant.stop()

    asyncio.run(main())
