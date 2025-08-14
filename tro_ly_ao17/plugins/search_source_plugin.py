import os
from typing import Any
from __main__  import ICommandHandler

class SearchSourceHandler(ICommandHandler):
    def __init__(self, root_folder: str = "."):
        self.root_folder = root_folder

    def can_handle(self, command: str) -> bool:
        return command.strip().lower().startswith("tìm kiếm từ khóa")

    def handle(self, command: str) -> bool:
        keyword = command.replace("tìm kiếm từ khóa", "").strip()
        if not keyword:
            print("❗ Vui lòng nhập từ khóa cần tìm.")
            return True

        print(f"🔍 Đang tìm kiếm từ khóa: '{keyword}' trong mã nguồn...")

        matches = self._search_keyword(keyword)
        if not matches:
            print("😥 Không tìm thấy kết quả phù hợp.")
            return True

        for file, line_num, content in matches:
            print(f"\n📁 {file} - dòng {line_num}:\n  ➤ {content.strip()}")

        print(f"\n✅ Hoàn tất. Tìm thấy {len(matches)} kết quả.")
        return True

    def _search_keyword(self, keyword: str):
        matches = []
        for foldername, _, filenames in os.walk(self.root_folder):
            for filename in filenames:
                if filename.endswith(('.py', '.txt', '.md', '.json', '.yaml', '.ini')):
                    full_path = os.path.join(foldername, filename)
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for i, line in enumerate(f, start=1):
                                if keyword.lower() in line.lower():
                                    matches.append((full_path, i, line))
                    except Exception as e:
                        print(f"⚠️ Không thể đọc file {full_path}: {e}")
        return matches

# ================= PLUGIN INFO =================

plugin_info = {
    "enabled": True,
    "register": lambda assistant: assistant.handlers.insert(1, SearchSourceHandler()),
    "methods": [],
    "classes": [],
    "description": "tìm kiếm từ khóa trong tất cả mã nguồn, thư mục, file"
}