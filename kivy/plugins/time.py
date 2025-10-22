import datetime

class TimePlugin:
    def can_handle(self, command: str) -> bool:
        return command in ["mấy giờ rồi", "bây giờ là mấy giờ"]

    def handle(self, command: str) -> str:
        now = datetime.datetime.now().strftime("%H:%M:%S")
        return f"⏰ Bây giờ là {now}"

def register(assistant):
    assistant.handlers.append(TimePlugin())

plugin_info = {
    "enabled": True,
    "register": register,
    "command_handle": ["mấy giờ rồi", "bây giờ là mấy giờ"]
}