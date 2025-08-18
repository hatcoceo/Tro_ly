# plugins/chat_logger.py
import builtins
from datetime import datetime

plugin_info = {
    "enabled": True,
    "register": lambda assistant: register_logger_plugin(assistant),
}

LOG_FILE = "chat_log.txt"


def register_logger_plugin(assistant):
    original_process = assistant.process_command

    # Biến lưu tạm input + buffer output
    assistant.pending_user_input = None
    assistant.output_buffer = []

    def new_process(command: str) -> bool:
        assistant.pending_user_input = command
        assistant.output_buffer = []  # Reset buffer
        custom_print.logging_active = True

        result = original_process(command)

        # Ghi log sau khi assistant trả lời xong
        if assistant.output_buffer:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user_input = assistant.pending_user_input or ""
            assistant_response = "\n".join(assistant.output_buffer)

            log_entry = (
                f"[{timestamp}] 👨‍💻User: {user_input}\n"
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
        assistant.output_buffer = []

        return result

    assistant.process_command = new_process

    # Ghi đè print
    original_print = builtins.print

    def custom_print(*args, **kwargs):
        output_text = " ".join(str(arg) for arg in args)

        if getattr(custom_print, "logging_active", False):
            assistant.output_buffer.append(output_text)

        original_print(*args, **kwargs)

    custom_print.logging_active = False
    builtins.print = custom_print