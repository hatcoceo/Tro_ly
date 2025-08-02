# có chế độ chạy chậm 
# sử dụng : chạy macro thứ bảy 2.5
import os
import sys
import time

macro_folder = "macros"
os.makedirs(macro_folder, exist_ok=True)

recorder_is_playing = False

class MacroRecorder:
    def __init__(self):
        self.recording = False
        self.commands = []
        self.current_macro_name = None

    def start(self, macro_name):
        if self.recording:
            print(f"⚠️ Đang ghi macro '{self.current_macro_name}'. Dừng lại trước.")
            return
        self.recording = True
        self.commands = []
        self.current_macro_name = macro_name
        print(f"🔴 Bắt đầu ghi macro: {macro_name}")

    def stop(self):
        if not self.recording:
            print("⚠️ Không có macro nào đang được ghi.")
            return

        path = os.path.join(macro_folder, f"{self.current_macro_name}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(self.commands))

        print(f"🟢 Đã lưu macro ({len(self.commands)} lệnh) vào: {path}")
        self.recording = False
        self.commands = []
        self.current_macro_name = None

    def record(self, command: str):
        if (
            self.recording and
            not recorder_is_playing and
            command.strip() and
            not command.startswith(("ghi macro ", "dừng ghi macro", "chạy macro "))
        ):
            self.commands.append(command.strip())

recorder = MacroRecorder()

class MacroCommandHandler:
    def __init__(self, assistant):
        self.assistant = assistant
        self._original_input = sys.stdin
        self._install_input_hook()

    def _install_input_hook(self):
        class MacroInputWrapper:
            def __init__(self, original):
                self.original = original

            def readline(self):
                user_input = self.original.readline()
                recorder.record(user_input)
                return user_input

        sys.stdin = MacroInputWrapper(sys.stdin)

    def can_handle(self, command: str) -> bool:
        return command.startswith(("ghi macro ", "dừng ghi macro", "chạy macro "))

    def handle(self, command: str) -> bool:
        if command.startswith("ghi macro "):
            recorder.start(command[10:].strip())
            return True

        elif command == "dừng ghi macro":
            recorder.stop()
            return True

        elif command.startswith("chạy macro "):
            # Tách macro name và delay thông minh
            rest = command[11:].strip()
            if not rest:
                print("❌ Thiếu tên macro.")
                return True

            delay = 1.0
            macro_name = rest

            # Nếu có khoảng trắng cuối cùng và phần sau là số -> coi là delay
            if " " in rest:
                try:
                    possible_delay = rest.split()[-1]
                    delay = float(possible_delay)
                    macro_name = rest[:rest.rfind(possible_delay)].strip()
                except ValueError:
                    delay = 1.0  # giữ nguyên toàn bộ làm tên macro nếu không chuyển được

            self._play_macro(macro_name, delay)
            return True

        return False

    def _play_macro(self, macro_name, delay=1.0):
        global recorder_is_playing
        path = os.path.join(macro_folder, f"{macro_name}.txt")
        if not os.path.exists(path):
            print(f"❌ Không tìm thấy macro: {macro_name}")
            return

        print(f"🏃 Đang chạy macro: {macro_name} (delay: {delay:.1f}s)")
        recorder_is_playing = True
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    cmd = line.strip()
                    if cmd:
                        print(f"⏩ {cmd}")
                        self.assistant.process_command(cmd)
                        time.sleep(delay)
        finally:
            recorder_is_playing = False

plugin_info = {
    "enabled": True,
    "register": lambda assistant: (
        assistant.handlers.insert(0, MacroCommandHandler(assistant))
    ),
    "methods": [],
    "classes": [],
    "description": "chạy lệnh tự động từ file txt"
}