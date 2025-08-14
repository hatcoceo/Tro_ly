# plugins/switch_version_manager.py

from typing import TYPE_CHECKING
from __main__ import Loader, ICommandHandler, IVersionManager

if TYPE_CHECKING:
    from __main__  import VirtualAssistantCore

class SwitchVersionManagerHandler(ICommandHandler):
    def __init__(self, assistant: 'VirtualAssistantCore'):
        self.assistant = assistant

    def can_handle(self, command: str) -> bool:
        return command.lower().startswith("dùng version manager")

    def handle(self, command: str) -> bool:
        name = command.replace("dùng version manager", "").strip()
        if not name:
            print("⚠️ Bạn cần chỉ định tên VersionManager.")
            return True

        try:
            # Bỏ qua info_attribute để load cả những VM bị "disabled"
            implementations = Loader._load_classes_from_folder(
                "version_managers",
                base_class=IVersionManager,
                info_attribute=None  # 👈 Bỏ qua kiểm tra enabled
            )

            for impl in implementations:
                if impl.__name__.lower() == name.lower():
                    instance = impl()
                    # Giữ lại version data nếu muốn
                    instance.versions = self.assistant.version_manager.versions
                    self.assistant.version_manager = instance
                    print(f"✅ Đã chuyển sang VersionManager: {impl.__name__}")
                    return True

            print(f"⚠️ Không tìm thấy VersionManager tên: {name}")
        except Exception as e:
            print(f"❌ Lỗi khi chuyển VersionManager: {e}")
        return True

# plugin_info để được nạp
plugin_info = {
    "enabled": True,
    "register": lambda assistant: assistant.handlers.insert (3, SwitchVersionManagerHandler(assistant)),
}