
# gợi ý trả lời sử dụng thư viện difflib
# plugin này của rieng tro_ly_ao3
import os
from typing import List
import difflib

FILE_PATH = "tri_thuc.txt"

class TriThucResponder:
    def __init__(self, similarity_thresh: float = 0.6):
        self.data = self.load_data()
        self.similarity_thresh = similarity_thresh

    def load_data(self) -> List[str]:
        if not os.path.exists(FILE_PATH):
            return []
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if "||" in line]

    def match_exact(self, query: str) -> List[str]:
        """Khớp tuyệt đối."""
        return [
            ans.strip()
            for line in self.data
            if (parts := line.split("||", 1))[0].strip().lower() == query.lower()
            for ans in [parts[1]]
        ]

    def match_similar(self, query: str) -> List[str]:
        """Gợi ý gần giống trên mức similarity_thresh."""
        candidates = []
        for line in self.data:
            question, answer = line.split("||", 1)
            similarity = difflib.SequenceMatcher(None, query.lower(), question.lower().strip()).ratio()
            if similarity >= self.similarity_thresh:
                candidates.append(line)
        return candidates

    def answer(self, query: str) -> str:
        """Trả lời câu hỏi, ưu tiên tuyệt đối, nếu không có thì gợi ý gần giống."""
        matches = self.match_exact(query)
        if matches:
            return "\n".join(f"✅ {ans}" for ans in matches)

        candidates = self.match_similar(query)
        if not candidates:
            return "🤷‍♂️ Không tìm thấy câu trả lời phù hợp - answers_plugin"

        self.suggestions = candidates
        suggestions_text = "\n".join(
            f"{i+1}. {line.split('||')[0].strip()}"
            for i, line in enumerate(self.suggestions)
        )
        return (
            "🤔 Không tìm thấy khớp tuyệt đối.\n"
            "Bạn có thể thử chọn một trong các gợi ý gần giống:\n"
            f"{suggestions_text}\n👉 Trả lời bằng số thứ tự."
        )

    def answer_index(self, index: int) -> str:
        """Trả lời khi chọn số gợi ý."""
        if not hasattr(self, "suggestions") or not (0 <= index - 1 < len(self.suggestions)):
            return "❌ Số không hợp lệ hoặc không có gợi ý nào."
        return f"💡 {self.suggestions[index - 1].split('||')[1].strip()}"


class TriThucHandler:
    """Handler tích hợp với hệ thống trợ lý ảo."""
    def __init__(self, core, similarity_thresh: float = 0.6):
        self.core = core
        self.responder = TriThucResponder(similarity_thresh)
        self.awaiting_choice = False

    def can_handle(self, command: str) -> bool:
        """Bỏ qua các lệnh CRUD."""
        crud_prefixes = ["thêm:", "xem", "sửa:", "xóa:"]
        return not any(command.lower().startswith(p) for p in crud_prefixes)

    def handle(self, command: str) -> bool:
        """Xử lý nhập liệu, bao gồm chọn số trong gợi ý."""
        if self.awaiting_choice and command.isdigit():
            result = self.responder.answer_index(int(command))
            self.awaiting_choice = False
        else:
            result = self.responder.answer(command)
            if result.startswith("🤔"):
                self.awaiting_choice = True
        print(result)
        return True


# ===== Plugin metadata =====
def register(core):
    handler = TriThucHandler(core)
    core.handlers.append(handler)
#    core.handlers.insert(1, handler)

plugin_info = {
   "enabled": True,
    "register": register,
    "classes": [
        {
            "class_name": "TriThucResponder",
            "version": "v1",
            "class_ref": TriThucResponder,
        }
    ]
}
