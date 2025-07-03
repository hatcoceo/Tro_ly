import os

FILE_PATH = "tri_thuc.txt"

class KnowledgeSearcher:
    def search(self, keyword: str) -> str:
        if not os.path.exists(FILE_PATH):
            return "📄 File tri_thuc.txt chưa tồn tại."

        with open(FILE_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        matched = [(i + 1, line.strip()) for i, line in enumerate(lines) if keyword.lower() in line.lower()]
        if not matched:
            return f"🔍 Không tìm thấy dòng nào chứa: '{keyword}'"

        return "\n".join(f"{i}. {line}" for i, line in matched)

class SearchCommandHandler:
    def __init__(self, core):
        self.core = core

    def can_handle(self, command: str) -> bool:
        return command.lower().startswith("tìm:")

    def handle(self, command: str) -> bool:
        keyword = command[4:].strip()
        if not keyword:
            print("❗ Vui lòng nhập từ khóa cần tìm. Ví dụ: tìm: Einstein")
            return True

        result = self.core.call_method("KnowledgeManager", "search", keyword, version="v1")

        if result is None:
            print("⚠️ Không có phương thức tìm kiếm nào được đăng ký.")
        elif isinstance(result, dict):
            print("🧠 Kết quả từ nhiều phiên bản:")
            for ver, res in result.items():
                print(f"\n🔹 [phiên bản: {ver}]\n{res}")
        elif isinstance(result, tuple):
            print("🧠 Kết quả từ nhiều phương thức (append):")
            for idx, res in enumerate(result, 1):
                print(f"\n🔹 Kết quả {idx}:\n{res}")
        else:
            print(result)

        return True

def register2(core):
    core.handlers.append(SearchCommandHandler(core))

plugin_info = {
  "enabled": True,
    "register": register2,
    "methods": [
        {
            "class_name": "KnowledgeManager",
            "method_name": "search",
            "version": "v1",
            "function": KnowledgeSearcher().search,
            "description": "Tìm kiếm đơn giản theo từ khóa trong tri_thuc.txt",
            "mode": "replace"
        }
    ]
}