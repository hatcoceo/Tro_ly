from datetime import datetime
from lunarcalendar import Converter, Solar, Lunar
from typing import List


class TodayCommandHandler:

    def __init__(self):
        self.vn_weekdays = ['Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm',
            'Thứ Sáu', 'Thứ Bảy', 'Chủ Nhật']

    def can_handle(self, command: str) -> bool:
        command = command.lower()
        return any(kw in command for kw in ['hôm nay là thứ', 'nay là thứ',
            'hôm nay thứ mấy', 'ngày âm là mấy'])

    def handle(self, command: str) -> str:
        now = datetime.now()
        weekday = self.vn_weekdays[now.weekday()]
        solar_date = now.strftime('%d/%m/%Y')
        
        try:
            # Tạo đối tượng Solar và chuyển đổi sang Lunar
            solar = Solar(now.year, now.month, now.day)
            lunar = Converter.Solar2Lunar(solar)
            lunar_date = f'{lunar.day}/{lunar.month}/{lunar.year}'
            
            # Trả về kết quả đầy đủ
            return f"Hôm nay là {weekday}\nNgày dương: {solar_date}\nNgày âm: {lunar_date}"
            
        except Exception as e:
            # Nếu có lỗi khi chuyển đổi âm lịch, chỉ trả về ngày dương
            print(f"Lỗi chuyển đổi âm lịch: {e}")
            return f"Hôm nay là {weekday}, ngày {solar_date}"


plugin_info = {'enabled': True, 
               'register': lambda assistant: assistant.handlers.append(TodayCommandHandler()), 
               'methods': [], 
               'classes': [],
               'command_handle': ['hôm nay là thứ']}