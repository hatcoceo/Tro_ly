from translate import Translator
from asistanst52 import ICommandHandler

# Handler thực hiện dịch
class TranslateCommandHandler(ICommandHandler):
    def can_handle(self, command: str) -> bool:
        return command.strip().lower().startswith("dịch:")

    def handle(self, command: str) -> bool:
        try:
            _, text = command.split(":", 1)
            translator = Translator(from_lang="vi", to_lang="en")
            result = translator.translate(text.strip())
            print(f"🌐 Dịch: {result}")
        except Exception as e:
            print(f"❌ Lỗi khi dịch: {e}")
        return True


# Hàm register, Core sẽ gọi hàm này
def register(core):
    core.handlers.insert (3, TranslateCommandHandler())

plugin_info = {
    "enabled": True,
    "register": register,
    "methods": [],
    "classes": [],
    "interfaces": [],
}