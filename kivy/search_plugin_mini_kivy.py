import os
from typing import List, Tuple


class KnowledgeSearcher:

    def __init__(self):
        self.file_path = 'tri_thuc.txt'
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Đảm bảo file tồn tại"""
        if not os.path.exists(self.file_path):
            open(self.file_path, 'w', encoding="utf-8").close()

    def search(self, keyword: str) -> List[Tuple[int, str]]:
        """Tìm kiếm theo từ khóa và trả về danh sách kết quả"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        results = []
        for idx, line in enumerate(lines, 1):
            if keyword.lower() in line.lower():
                results.append((idx, line))
        return results


class SearchHandler:

    def __init__(self):
        self.searcher = KnowledgeSearcher()

    def can_handle(self, command: str) -> bool:
        """Xác định xem có phải lệnh tìm kiếm không (bắt đầu bằng 'tìm:')"""
        return command.lower().startswith('tìm:')

    def handle(self, command: str) -> str:
        """Xử lý lệnh tìm kiếm"""
        keyword = command[4:].strip()
        if not keyword:
            return "❗ Vui lòng nhập từ khóa cần tìm. Ví dụ: tìm: python"

        results = self.searcher.search(keyword)
        if not results:
            return f"🔍 Không tìm thấy kết quả cho '{keyword}'"

        # Ghép nhiều dòng kết quả lại thành chuỗi
        lines = [f"{idx}. {line}" for idx, line in results]
        return f"🔍 Kết quả tìm kiếm cho '{keyword}':\n" + "\n".join(lines)


# Thông tin plugin để assistant có thể load
plugin_info = {
    'enabled': True,
    'register': lambda assistant: assistant.handlers.append(SearchHandler())
}