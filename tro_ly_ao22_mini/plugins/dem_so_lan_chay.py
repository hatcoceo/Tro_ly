import os
import json
from typing import Any
COUNT_FILE = os.path.join(os.path.dirname(__file__), 'run_count.json')


def register(assistant: Any) ->None:
    """Hàm được gọi khi plugin được tải – thực hiện đếm và thông báo"""
    count = 0
    if os.path.exists(COUNT_FILE):
        try:
            with open(COUNT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                count = data.get('run_count', 0)
        except (json.JSONDecodeError, IOError):
            pass
    count += 1
    with open(COUNT_FILE, 'w', encoding='utf-8') as f:
        json.dump({'run_count': count}, f)
    print(f'📊 Trợ lý đã được chạy {count} lần (kể cả lần này).')


plugin_info = {'enabled': True, 'register': register, 'command_handle': []}
