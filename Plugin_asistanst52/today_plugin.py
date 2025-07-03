from datetime import datetime
from lunarcalendar import Converter, Solar, Lunar
from typing import List
from asistanst50 import ICommandHandler  # chỉnh lại đường import phù hợp tên dự án của bạn

# Nếu không cài sẵn thư viện lunarcalendar thì cài:
# pip install lunarcalendar

class TodayHandler(ICommandHandler):
    def can_handle(self, command: str) -> bool:
        keywords = ["hôm nay là thứ", "nay là thứ", "hôm nay thứ mấy", "today"]
        return any(kw in command.lower() for kw in keywords)

    def handle(self, command: str) -> bool:
        today = datetime.now()
        weekday_vn = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
        weekday = weekday_vn[today.weekday()]

        solar = Solar(today.year, today.month, today.day)
        lunar = Converter.Solar2Lunar(solar)

        lunar_date = f"{lunar.day}/{lunar.month}/{lunar.year}"
        solar_date = today.strftime("%d/%m/%Y")

        print(f"📅 Hôm nay là {weekday}, ngày {solar_date} (Dương lịch)")
        print(f"🌙 Âm lịch: {lunar_date}")
        return True

def register(va_core):
    handler = TodayHandler()
    va_core.handlers.append(handler)

plugin_info = {
    "enabled": True,
    "register": register,
    "methods": [],
    "classes": [],
   # "interfaces": []
}