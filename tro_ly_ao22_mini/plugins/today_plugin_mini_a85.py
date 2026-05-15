from datetime import datetime
from lunarcalendar import Converter, Solar
from typing import Dict


class TodayCommandHandler:

    def __init__(self):
        self.vn_weekdays = [
            'Thứ Hai',
            'Thứ Ba',
            'Thứ Tư',
            'Thứ Năm',
            'Thứ Sáu',
            'Thứ Bảy',
            'Chủ Nhật'
        ]

    def can_handle(self, command: str) -> bool:
        command = command.lower()

        return any(kw in command for kw in [
            'hôm nay là thứ',
            'nay là thứ',
            'hôm nay thứ mấy',
            'ngày âm là mấy'
        ])

    def handle(self, command: str) -> Dict:

        now = datetime.now()

        weekday = self.vn_weekdays[now.weekday()]
        solar_date = now.strftime('%d/%m/%Y')

        solar = Solar(now.year, now.month, now.day)
        lunar = Converter.Solar2Lunar(solar)

        lunar_date = f'{lunar.day}/{lunar.month}/{lunar.year}'

        # Vẫn in ra terminal như cũ
        print(f'\n📅 {weekday}, ngày {solar_date} (Dương lịch)')
        print(f'🌙 {lunar_date} (Âm lịch)\n')

        # Trả dữ liệu cho plugin khác
        return {
            "success": True,
            "weekday": weekday,
            "solar_date": solar_date,
            "lunar_date": lunar_date,
            "text": f"{weekday}, ngày {solar_date} - Âm lịch: {lunar_date}"
        }


plugin_info = {
    'enabled': True,
    'register': lambda assistant: assistant.handlers.append(TodayCommandHandler()),
    'methods': [],
    'classes': [],
    'command_handle': ['hôm nay là thứ']
}