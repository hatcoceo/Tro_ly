import webbrowser
from typing import Any, List, Optional


class BrowserHandler:
    """Xử lý lệnh mở trình duyệt web"""

    def __init__(self):
        self.triggers = ['mở trình duyệt', 'open web', 'browser', 'mở web']

    def can_handle(self, command: str) ->bool:
        """Kiểm tra lệnh có khớp với một trigger không"""
        cmd_lower = command.lower().strip()
        for trigger in self.triggers:
            if cmd_lower.startswith(trigger):
                return True
        return False

    def handle(self, command: str) ->None:
        """Thực hiện mở URL trong trình duyệt"""
        cmd_lower = command.lower().strip()
        url = None
        for trigger in self.triggers:
            if cmd_lower.startswith(trigger):
                remaining = cmd_lower[len(trigger):].strip()
                if remaining:
                    url = remaining
                break
        if not url:
            url = 'https://www.google.com'
            print('🌐 Không có URL, mở Google mặc định.')
        elif not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        try:
            webbrowser.open(url)
            print(f'✅ Đã mở trình duyệt: {url}')
        except Exception as e:
            print(f'❌ Không thể mở trình duyệt: {e}')


plugin_info = {'enabled': True, 'register': lambda assistant: _register(
    assistant), 'command_handle': ['mở trình duyệt', 'open web', 'browser',
    'mở web']}


def _register(assistant: Any) ->None:
    """Đăng ký handler trình duyệt vào trợ lý"""
    handler = BrowserHandler()
    assistant.handlers.append(handler)
    print('🌐 Plugin Trình duyệt đã sẵn sàng.')
