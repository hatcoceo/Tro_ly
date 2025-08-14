# plugins/plugin_a.py

def add(a: int, b: int) -> int:
    print(f"[PluginA] Cộng {a} + {b}")
    return a + b

plugin_info = {
    "enabled": True,
    "register": None,
    "methods": [
        {
            "class_name": "MathPluginA",
            "method_name": "add",
            "version": "1.0",
            "function": add,
            "description": "Hàm cộng hai số",
        }
    ],
    "classes": []
}