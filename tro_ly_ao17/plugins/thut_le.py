# sd1: hiển thị thụt lề demo.py
# sd2: phục hồi thụt lề demo_indent.py
from __main__ import ICommandHandler
import os

class IndentVisualizerHandler(ICommandHandler):
    def can_handle(self, command: str) -> bool:
        return (
            command.startswith("hiển thị thụt lề") or 
            command.startswith("indent") or 
            command.startswith("phục hồi thụt lề") or 
            command.startswith("restore indent")
        )

    def handle(self, command: str) -> bool:
        command = command.strip()

        if command.startswith("hiển thị thụt lề") or command.startswith("indent"):
            filepath = command.replace("hiển thị thụt lề", "").replace("indent", "").strip()
            if not filepath:
                print("⚠️ Cú pháp: hiển thị thụt lề <đường_dẫn_file.py>")
                return True
            if not os.path.exists(filepath):
                print(f"❌ Không tìm thấy file: {filepath}")
                return True

            base, ext = os.path.splitext(filepath)
            output_path = base + "_indent" + ext

            tab_size = 4
            with open(filepath, "r", encoding="utf-8") as f_in, open(output_path, "w", encoding="utf-8") as f_out:
                for i, line in enumerate(f_in, 1):
                    original_line = line
                    line = line.replace('\t', ' ' * tab_size)  # Convert tabs to spaces

                    indent_count = len(line) - len(line.lstrip(' '))
                    level = indent_count // tab_size + 1  # cộng 1 nếu muốn thụt thêm
                    remainder = indent_count % tab_size
                    indicator = "---|" * level + "." * remainder

                    warn = ""
                    if '\t' in original_line:
                        warn += " [⚠️ Có ký tự tab]"
                    if remainder != 0:
                        warn += f" [⚠️ Không chia hết cho {tab_size}]"

                    f_out.write(f"{indicator}{line.lstrip().rstrip()}{warn}\n")

            print(f"✅ Đã ghi kết quả hiển thị thụt lề vào: {output_path}")
            return True

        if command.startswith("phục hồi thụt lề") or command.startswith("restore indent"):
            filepath = command.replace("phục hồi thụt lề", "").replace("restore indent", "").strip()
            if not filepath:
                print("⚠️ Cú pháp: phục hồi thụt lề <đường_dẫn_file_indent.py>")
                return True
            if not os.path.exists(filepath):
                print(f"❌ Không tìm thấy file: {filepath}")
                return True

            base, ext = os.path.splitext(filepath)
            if "_indent" in base:
                base = base.replace("_indent", "")
            output_path = base + "_restored" + ext

            with open(filepath, "r", encoding="utf-8") as f_in, open(output_path, "w", encoding="utf-8") as f_out:
                for line in f_in:
                    restored_line = self._restore_indentation(line)
                    f_out.write(restored_line)

            print(f"✅ Đã phục hồi file và ghi vào: {output_path}")
            return True

        return False

    def _restore_indentation(self, line: str, tab_size: int = 4) -> str:
        count = 0
        while line.startswith("---|"):
            line = line[len("---|"):]
            count += 1

        remainder = 0
        while line.startswith("."):
            line = line[1:]
            remainder += 1

        # Loại bỏ cảnh báo nếu có
        line = line.split("[⚠️")[0].rstrip()

        return " " * (count * tab_size + remainder) + line + "\n"

plugin_info = {
    "enabled": True,
    "methods": [],
    "classes": [],
    "description": "hiển thị và phục hồi thụt lề trực quan cho file Python",
    "register": lambda assistant: assistant.handlers.insert(3, IndentVisualizerHandler())
}