
import os
import re
from typing import Any, List, Callable, Optional, Tuple
from abc import ABC, abstractmethod
# Interface mới với các phương thức CRUD
class IDataFileHandler(ABC):
    @abstractmethod
    def open_file(self, file_path: str) -> None:
        """Mở file dữ liệu"""
        pass

    @abstractmethod
    def read_data(self) -> Any:
        """Đọc toàn bộ dữ liệu từ file"""
        pass

    @abstractmethod
    def write_data(self, data: Any) -> None:
        """Ghi đè dữ liệu mới vào file hiện tại"""
        pass

    @abstractmethod
    def save_file(self, file_path: str = None) -> None:
        """Lưu file. Nếu truyền file_path thì lưu vào file mới"""
        pass

    @abstractmethod
    def close_file(self) -> None:
        """Đóng file đang mở"""
        pass

    # CRUD methods
    @abstractmethod
    def add_record(self, record: Any) -> None:
        """Thêm một record (dòng) mới vào dữ liệu hiện tại"""
        pass

    @abstractmethod
    def get_record(self, index: int) -> Any:
        """Lấy một record theo chỉ số"""
        pass

    @abstractmethod
    def find_records(self, condition: Callable[[Any], bool]) -> List[Any]:
        """Tìm các record thoả mãn điều kiện"""
        pass

    @abstractmethod
    def update_record(self, index: int, new_record: Any) -> None:
        """Cập nhật record tại vị trí index bằng record mới"""
        pass

    @abstractmethod
    def delete_record(self, index: int) -> None:
        """Xoá record tại vị trí index"""
        pass

# Base DataFileHandler
class BaseDataFileHandler(IDataFileHandler):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.lines = []
        self.is_open = False
        self.cached_data = None
        
    def open_file(self, file_path: str = None) -> None:
        if file_path:
            self.file_path = file_path
        self.is_open = True
        self._refresh_cache()
        
    def _refresh_cache(self):
        """Làm mới dữ liệu cache từ file"""
        if not os.path.exists(self.file_path):
            self.lines = []
            self.cached_data = []
            return
            
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.lines = f.readlines()
        self.cached_data = [line.strip() for line in self.lines]

    def read_data(self) -> List[str]:
        if not self.is_open:
            raise RuntimeError("File chưa được mở")
        return self.cached_data

    def write_data(self, data: List[str]) -> None:
        if not self.is_open:
            raise RuntimeError("File chưa được mở")
            
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(data))
        self._refresh_cache()

    def save_file(self, file_path: str = None) -> None:
        if file_path:
            self.file_path = file_path
        self.write_data(self.cached_data)

    def close_file(self) -> None:
        self.is_open = False
        self.lines = []
        self.cached_data = []

    # CRUD implementations
    def add_record(self, record: str) -> None:
        if not self.is_open:
            raise RuntimeError("File chưa được mở")
            
        self.cached_data.append(record.strip())
        with open(self.file_path, 'a', encoding='utf-8') as f:
            f.write(record.strip() + "\n")
        self._refresh_cache()

    def get_record(self, index: int) -> str:
        if not self.is_open:
            raise RuntimeError("File chưa được mở")
        if index < 0 or index >= len(self.cached_data):
            raise IndexError("Chỉ mục nằm ngoài phạm vi")
        return self.cached_data[index]

    def find_records(self, condition: Callable[[str], bool]) -> List[Tuple[int, str]]:
        if not self.is_open:
            raise RuntimeError("File chưa được mở")
        return [(i, record) for i, record in enumerate(self.cached_data) if condition(record)]

    def update_record(self, index: int, new_record: str) -> None:
        if not self.is_open:
            raise RuntimeError("File chưa được mở")
        if index < 0 or index >= len(self.cached_data):
            raise IndexError("Chỉ mục nằm ngoài phạm vi")
            
        self.cached_data[index] = new_record.strip()
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(self.cached_data))
        self._refresh_cache()

    def delete_record(self, index: int) -> None:
        if not self.is_open:
            raise RuntimeError("File chưa được mở")
        if index < 0 or index >= len(self.cached_data):
            raise IndexError("Chỉ mục nằm ngoài phạm vi")
            
        del self.cached_data[index]
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(self.cached_data))
        self._refresh_cache()

# Triển khai nghiệp vụ sử dụng interface mới
FILE_PATH = "tri_thuc.txt"
TEMP_FILE = "delete_candidates.txt"

class KnowledgeManager:
    def __init__(self):
        self.file_handler = BaseDataFileHandler(FILE_PATH)
        self.file_handler.open_file()
        
    def add(self, data: str) -> str:
        self.file_handler.add_record(data)
        return "✅ Đã thêm dòng kiến thức - crud2_plugin."

    def read(self) -> str:
        data = self.file_handler.read_data()
        if not data:
            return "📭 Không có dữ liệu."
        return "\n".join(f"{i+1}. {line}" for i, line in enumerate(data))

    def update(self, line_number: int, new_data: str) -> str:
        try:
            self.file_handler.update_record(line_number - 1, new_data)
            return f"✅ Đã cập nhật dòng {line_number}."
        except IndexError:
            return "❌ Số dòng không hợp lệ."

    def delete_by_keyword(self, keyword: str) -> str:
        keyword = keyword.strip().lower()
        
        # Tìm kiếm chính xác
        exact_matches = self.file_handler.find_records(
            lambda r: r.split("||")[0].strip().lower() == keyword
        )
        
        if exact_matches:
            # Xóa tất cả các bản ghi khớp
            for idx, _ in sorted(exact_matches, reverse=True):
                self.file_handler.delete_record(idx)
                
            deleted_items = "\n".join(f"• {record}" for _, record in exact_matches)
            return f"🗑️ Đã xóa các dòng:\n{deleted_items} - crud2_plugin."
        
        # Tìm kiếm gần đúng nếu không có kết quả chính xác
        similar_matches = self.file_handler.find_records(
            lambda r: keyword in r.lower()
        )
        
        if not similar_matches:
            return "🔎 Không tìm thấy dữ liệu phù hợp để xóa."
            
        # Lưu kết quả tạm thời và trả về UI
        self._save_candidates([record for _, record in similar_matches])
        
        result_lines = []
        for i, (idx, record) in enumerate(similar_matches, 1):
            result_lines.append(f"{i}. [Dòng {idx+1}] {record}")
        
        return (
            "🔎 Tìm thấy các dòng gần giống:\n" +
            "\n".join(result_lines) +
            "\n👉 Gõ: xóa_chọn:<số thứ tự> để xóa dòng tương ứng."
        )

    def delete_by_index(self, select_number: int) -> str:
        try:
            # Đọc danh sách ứng viên từ file tạm
            temp_handler = BaseDataFileHandler(TEMP_FILE)
            temp_handler.open_file()
            candidates = temp_handler.read_data()
            temp_handler.close_file()
            
            if select_number < 1 or select_number > len(candidates):
                return "❌ Số thứ tự không hợp lệ."
                
            target_record = candidates[select_number - 1]
            
            # Tìm và xóa bản ghi tương ứng
            matches = self.file_handler.find_records(lambda r: r == target_record)
            if not matches:
                return "❌ Không tìm thấy dòng cần xóa."
                
            self.file_handler.delete_record(matches[0][0])
            os.remove(TEMP_FILE)
            return f"🗑️ Đã xóa dòng: {target_record}"
            
        except Exception as e:
            return f"❌ Lỗi khi xóa: {str(e)}"

    def _save_candidates(self, candidates: List[str]) -> None:
        """Lưu danh sách ứng viên vào file tạm"""
        with open(TEMP_FILE, 'w', encoding='utf-8') as f:
            f.write("\n".join(candidates))

# Command handler không thay đổi
class CRUDCommandHandler:
    def __init__(self, core):
        self.core = core

    def can_handle(self, command: str) -> bool:
        return any(
            command.lower().startswith(prefix)
            for prefix in ["thêm:", "xem", "sửa:", "xóa:", "xóa_chọn:"]
        )

    def handle(self, command: str) -> bool:
        cmd = command.strip()

        if cmd.startswith("thêm:"):
            data = cmd[5:].strip()
            result = self.core.call_class_method("KnowledgeManager", "add", data, version="v1")

        elif cmd == "xem":
            result = self.core.call_class_method("KnowledgeManager", "read", version="v1")

        elif cmd.startswith("sửa:"):
            try:
                rest = cmd[4:].strip()
                line_number, new_text = rest.split(":", 1)
                result = self.core.call_class_method(
                    "KnowledgeManager", "update", int(line_number.strip()), new_text.strip(), version="v1"
                )
            except Exception:
                result = "❌ Cú pháp sửa không đúng. Dạng: sửa: <số dòng>: <nội dung mới>"

        elif cmd.startswith("xóa:"):
            keyword = cmd[4:].strip()
            result = self.core.call_class_method(
                "KnowledgeManager", "delete_by_keyword", keyword, version="v1"
            )

        elif cmd.startswith("xóa_chọn:"):
            try:
                number = int(cmd[len("xóa_chọn:"):].strip())
                result = self.core.call_class_method(
                    "KnowledgeManager", "delete_by_index", number, version="v1"
                )
            except:
                result = "❌ Cú pháp không đúng. Dạng: xóa_chọn:<số thứ tự>"

        else:
            result = "🤷‍♂️ Không hiểu yêu cầu CRUD - crud2_plugin."

        print(result)
        return True

def register(core):
    handler = CRUDCommandHandler(core)
    core.handlers.insert(4, handler)

plugin_info = {
   "enabled": True,
    "register": register,
    "classes": [
        {
            "class_name": "KnowledgeManager",
            "version": "v1",
            "class_ref": KnowledgeManager,
        }
    ]
}