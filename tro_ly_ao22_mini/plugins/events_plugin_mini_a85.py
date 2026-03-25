# sd1 [ sự kiện:  hôm nay trời mưa ]
import os
import json
from datetime import datetime
from typing import List, Dict, Optional


class EventHandler:

    def __init__(self, data_file='events.json'):
        self.data_file = data_file
        self.events: List[Dict] = []
        self.load_events()

    def load_events(self):
        """Tải dữ liệu sự kiện từ file JSON"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.events = json.load(f)
            except:
                self.events = []

    def save_events(self):
        """Lưu dữ liệu sự kiện ra file JSON"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.events, f, ensure_ascii=False, indent=2)

    def add_event(self, content: str):
        """Thêm sự kiện mới với ngày giờ hiện tại"""
        event = {'content': content, 'date': datetime.now().isoformat()}
        self.events.append(event)
        self.save_events()
        return event

    def find_event(self, keyword: str) ->Optional[Dict]:
        """Tìm sự kiện gần nhất chứa từ khóa"""
        for event in reversed(self.events):
            if keyword.lower() in event['content'].lower():
                return event
        return None

    def days_since_event(self, keyword: str) ->Optional[int]:
        """
        Tính số ngày đã trôi qua kể từ sự kiện,
        tính theo số lần qua nửa đêm (không tính đủ 24 giờ)
        """
        event = self.find_event(keyword)
        if not event:
            return None
        event_date = datetime.fromisoformat(event['date']).date()
        current_date = datetime.now().date()
        return (current_date - event_date).days


class EventCommandHandler:

    def __init__(self, event_handler: EventHandler):
        self.event_handler = event_handler
        self.event_prefix = 'sự kiện:'
        self.question_prefixes = ['bao lâu rồi', 'bao nhiêu ngày rồi',
            'mấy ngày rồi']

    def can_handle(self, command: str) ->bool:
        command_lower = command.lower()
        return command_lower.startswith(self.event_prefix) or any(
            command_lower.endswith(q) for q in self.question_prefixes)

    def handle(self, command: str) ->bool:
        command_lower = command.lower()
        if command_lower.startswith(self.event_prefix):
            event_content = command[len(self.event_prefix):].strip()
            if event_content:
                self.event_handler.add_event(event_content)
                print(f'📝 Đã ghi sự kiện: {event_content}')
            else:
                print("⚠️ Vui lòng nhập nội dung sự kiện sau 'sự kiện:'")
            return True
        keyword = command
        for q in self.question_prefixes:
            if keyword.lower().endswith(q):
                keyword = keyword[:-len(q)].strip()
                break
        if not keyword:
            print("⚠️ Vui lòng nhập từ khóa sự kiện (ví dụ: 'mưa bao lâu rồi')"
                )
            return True
        days = self.event_handler.days_since_event(keyword)
        if days is None:
            print(f"🔍 Không tìm thấy sự kiện nào về '{keyword}'")
        elif days == 0:
            print(f"⏱️ Sự kiện '{keyword}' xảy ra hôm nay")
        else:
            print(f"⏳ Sự kiện '{keyword}' đã xảy ra {days} ngày trước")
        return True


event_handler = EventHandler()
plugin_info = {'enabled': True, 'register': lambda core: core.handlers.
    append(EventCommandHandler(event_handler)), 'description':
    'Ghi chú sự kiện và tính toán số ngày đã trôi qua', 'methods': [{
    'class_name': 'EventCommandHandler', 'method_name': 'can_handle',
    'function': EventCommandHandler.can_handle, 'version': '1.0',
    'description': 'Kiểm tra khả năng xử lý lệnh'}, {'class_name':
    'EventCommandHandler', 'method_name': 'handle', 'function':
    EventCommandHandler.handle, 'version': '1.0', 'description':
    'Xử lý lệnh ghi chú/truy vấn sự kiện'}]}
