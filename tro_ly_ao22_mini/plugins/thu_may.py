from datetime import datetime

class DayOfWeekHandler:
    def can_handle(self, command: str) -> bool:
        keywords = [
            "thứ mấy"
        ]
        return any(k in command for k in keywords)

    def handle(self, command: str):
        today = datetime.now()

        # weekday(): Monday=0 ... Sunday=6
        days_vi = [
            "Thứ Hai",
            "Thứ Ba",
            "Thứ Tư",
            "Thứ Năm",
            "Thứ Sáu",
            "Thứ Bảy",
            "Chủ Nhật"
        ]

        day_name = days_vi[today.weekday()]

        print(day_name)      # vẫn giữ để hiển thị
        return day_name      # ✅ thêm dòng này để lấy được giá trị sử lý cho macro 

def register(assistant):
    assistant.handlers.append(DayOfWeekHandler())

plugin_info = {
    "enabled": True,
    "register": register,
    "command_handle": ["thứ mấy"]
}