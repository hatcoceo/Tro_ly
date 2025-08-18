plugin_info = {
    "enabled": True,
    "methods": [],
    "classes": [],
    "register": lambda assistant: assistant.handlers.insert(4, LabelDataHandler(assistant))
}

#from __main__  import ICommandHandler
import os

class LabelDataHandler():
    def __init__(self, assistant):
        self.assistant = assistant
        self.file_path = "tri_thuc.txt"
        self.label_output = "tri_thuc_labeled.txt"

    def can_handle(self, command: str) -> bool:
        return command.lower().startswith("dán nhãn dữ liệu")

    def handle(self, command: str) -> bool:
        if not os.path.exists(self.file_path):
            print(f"❌ Không tìm thấy file: {self.file_path}")
            return True

        # Lấy danh sách câu hỏi đã dán nhãn từ file output
        labeled_questions = set()
        if os.path.exists(self.label_output):
            with open(self.label_output, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split("||")
                    if len(parts) >= 1:
                        labeled_questions.add(parts[0].strip())

        print(f"📄 Đang đọc dữ liệu từ {self.file_path}")
        skipped = 0
        labeled = 0

        with open(self.label_output, "a", encoding="utf-8") as out_f:
            with open(self.file_path, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f.readlines(), 1):
                    line = line.strip()
                    if not line or "||" not in line:
                        continue

                    question, answer = map(str.strip, line.split("||", 1))

                    if question in labeled_questions:
                        skipped += 1
                        continue

                    print(f"\n📝 Mục {idx}:")
                    print(f"❓ Câu hỏi: {question}")
                    print(f"💬 Trả lời: {answer}")
                    label = input("🏷️ Nhập nhãn cho mục này (hoặc bỏ trống để bỏ qua): ").strip()

                    if label:
                        out_f.write(f"{question} || {answer} || {label}\n")
                        out_f.flush()
                        labeled += 1

        print(f"\n✅ Hoàn tất. Đã dán nhãn: {labeled} mục. Bỏ qua: {skipped} mục đã có nhãn.")
        return True