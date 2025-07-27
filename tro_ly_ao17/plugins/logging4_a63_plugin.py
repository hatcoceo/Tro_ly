# plugins/chat_logger.py

import builtins
from datetime import datetime
from __main__ import ProcessInput

plugin_info = {
    "enabled": True,
    "register": lambda assistant: register_logger_plugin(),
}

LOG_FILE = "chat_log.txt"

def register_logger_plugin():
    original_process = ProcessInput.process

    # Biến lưu tạm input + buffer output
    ProcessInput.pending_user_input = None
    ProcessInput.output_buffer = []

    def new_process(self, user_input: str) -> bool:
        ProcessInput.pending_user_input = user_input
        ProcessInput.output_buffer = []  # Reset buffer
        custom_print.logging_active = True

        result = original_process(self, user_input)

        # Ghi log sau khi assistant trả lời xong
        if ProcessInput.output_buffer:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user_input = ProcessInput.pending_user_input or ""
            assistant_response = "\n".join(ProcessInput.output_buffer)

            log_entry = (
                f"[{timestamp}] User: {user_input}\n"
                f"[{timestamp}] Assistant: {assistant_response}\n"
            )

            try:
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    old_content = f.read()
            except FileNotFoundError:
                old_content = ""

            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write(log_entry + old_content)

        # Tắt log
        custom_print.logging_active = False
        ProcessInput.output_buffer = []

        return result

    ProcessInput.process = new_process

    original_print = builtins.print

    def custom_print(*args, **kwargs):
        output_text = " ".join(str(arg) for arg in args)

        if getattr(custom_print, "logging_active", False):
            ProcessInput.output_buffer.append(output_text)

        original_print(*args, **kwargs)

    custom_print.logging_active = False
    builtins.print = custom_print