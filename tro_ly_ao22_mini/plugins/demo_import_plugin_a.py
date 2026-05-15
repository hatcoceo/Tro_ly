# plugins/plugin_time_utils.py
from datetime import datetime

def get_current_hour() -> int:
    """Trả về giờ hiện tại (0-23)"""
    return datetime.now().hour

# Plugin này chỉ cung cấp hàm, không đăng ký handler
plugin_info = {
    "enabled": True,
    "register": lambda assistant: None   # không làm gì cả
}