from datetime import datetime
from lunarcalendar import Converter, Solar, Lunar
from typing import List


class TodayCommandHandler:

    def __init__(self):
        self.vn_weekdays = ['Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm',
            'Thứ Sáu', 'Thứ Bảy', 'Chủ Nhật']

    def can_handle(self, command: str) ->bool:
        command = command.lower()
        return any(kw in command for kw in ['hôm nay là thứ', 'nay là thứ',
            'hôm nay thứ mấy', 'ngày âm là mấy'])

    def handle(self, command: str) ->bool:
        now = datetime.now()
        weekday = self.vn_weekdays[now.weekday()]
        solar_date = now.strftime('%d/%m/%Y')
        solar = Solar(now.year, now.month, now.day)
        lunar = Converter.Solar2Lunar(solar)
        lunar_date = f'{lunar.day}/{lunar.month}/{lunar.year}'
        print(f'\n📅 {weekday}, ngày {solar_date} (Dương lịch)')
        print(f'🌙 {lunar_date} (Âm lịch)\n')
        return True


plugin_info = {'enabled': True, 'register': lambda assistant: assistant.
    handlers.append(TodayCommandHandler()), 'methods': [], 'classes': [],
    'command_handle': ['hôm nay là thứ']}
