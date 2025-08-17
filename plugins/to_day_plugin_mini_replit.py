from datetime import datetime
from lunarcalendar import Converter, Solar


class TodayCommandHandler:
    def __init__(self):
        self.vn_weekdays = [
            "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm",
            "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"
        ]
        # Các từ khóa người dùng có thể hỏi
        self.keywords = [
            "hôm nay là thứ",
            "hôm nay thứ mấy",
            "hôm nay là thứ mấy",
            "nay là thứ",
            "nay thứ mấy",
            "ngày âm là mấy",
            "ngày âm hôm nay",
        ]

    def can_handle(self, command: str) -> bool:
        """Kiểm tra xem lệnh có thuộc plugin này không"""
        return any(kw in command for kw in self.keywords)

    def handle(self, command: str) -> str:
        """Xử lý và trả về ngày dương & âm lịch"""
        now = datetime.now()
        weekday = self.vn_weekdays[now.weekday()]
        solar_date = now.strftime("%d/%m/%Y")

        solar = Solar(now.year, now.month, now.day)
        lunar = Converter.Solar2Lunar(solar)
        lunar_date = f"{lunar.day}/{lunar.month}/{lunar.year}"

        response = (
            f"📅 {weekday}, ngày {solar_date} (Dương lịch)\n"
            f"🌙 {lunar_date} (Âm lịch)"
        )
        return response


plugin_info = {
    "enabled": True,
    "register": lambda assistant: assistant.handlers.append(TodayCommandHandler()),
    "command_handle": [
        "hôm nay là thứ",
        "hôm nay thứ mấy",
        "hôm nay là thứ mấy",
        "nay là thứ",
        "nay thứ mấy",
        "ngày âm là mấy",
        "ngày âm hôm nay",
    ],
}