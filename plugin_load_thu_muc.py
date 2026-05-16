# plugins/plugin_load_thu_muc.py
import os
import sys
import importlib.util

plugin_info = {
    "enabled": True,
    "register": lambda assistant: register(assistant)
}

def register(assistant):
    plugins_folder = assistant.loader.plugins_folder
    
    for item in os.listdir(plugins_folder):
        dir_path = os.path.join(plugins_folder, item)
        if not os.path.isdir(dir_path):
            continue
        
        init_file = os.path.join(dir_path, "__init__.py")
        if not os.path.isfile(init_file):
            continue
        
        try:
            package_name = item
            spec = importlib.util.spec_from_file_location(package_name, init_file)
            module = importlib.util.module_from_spec(spec)
            module.__package__ = package_name
            module.__path__ = [dir_path]
            sys.modules[package_name] = module  # Quan trọng!
            spec.loader.exec_module(module)
            
            pkg_info = getattr(module, "plugin_info", {})
            if pkg_info.get("enabled", True) and callable(pkg_info.get("register")):
                pkg_info["register"](assistant)
                print(f"✅ Đã tải plugin thư mục: {item}")
        except Exception as e:
            print(f"❌ Lỗi tải {item}: {e}")