import os
from typing import List, Tuple


class KnowledgeSearcher:

    def __init__(self):
        self.file_path = 'tri_thuc.txt'
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Đảm bảo file tồn tại"""
        if not os.path.exists(self.file_path):
            open(self.file_path, 'w').close()

    def search(self, keyword: str) ->List[Tuple[int, str]]:
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

    def can_handle(self, command: str) ->bool:
        """Xử lý các lệnh bắt đầu bằng 'tìm:'"""
        return command.lower().startswith('tìm:')

    def handle(self, command: str) ->bool:
        """Xử lý lệnh tìm kiếm"""
        keyword = command[4:].strip()
        if not keyword:
            print('❗ Vui lòng nhập từ khóa cần tìm. Ví dụ: tìm: python')
            return True
        results = self.searcher.search(keyword)
        if not results:
            print(f"🔍 Không tìm thấy kết quả cho '{keyword}'")
        else:
            print(f"🔍 Kết quả tìm kiếm cho '{keyword}':")
            for idx, line in results:
                print(f'{idx}. {line}')
        return True


plugin_info = {'enabled': True, 'register': lambda assistant: assistant.
    handlers.append(SearchHandler())}
