# save_chat.py - Plugin lưu lịch sử hội thoại ra file .txt
import os
import sys
import time
from datetime import datetime
from typing import Any, List, Dict

# Biến toàn cục để lưu lịch sử hội thoại (chỉ dùng trong plugin này)
_chat_history: List[str] = []
_original_print = None
_original_process_command = None

class SaveChatHandler:
    """Xử lý lệnh lưu hội thoại"""
    
    def can_handle(self, command: str) -> bool:
        """Kiểm tra xem lệnh có phải là lệnh lưu hội thoại không"""
        cmd = command.strip().lower()
        return cmd in ['lưu hội thoại', 'save chat', 'lưu chat', 'save_conversation']
    
    def handle(self, command: str) -> None:
        """Thực hiện lưu hội thoại ra file txt"""
        global _chat_history
        
        # Hỏi tên file từ người dùng
        filename = input("📝 Nhập tên file (không cần đuôi .txt): ").strip()
        if not filename:
            print("❌ Tên file không được để trống!")
            return
        
        # Thêm đuôi .txt nếu chưa có
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        try:
            # Lưu nội dung hội thoại vào file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"=== LƯU HỘI THOẠI ===\n")
                f.write(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*40}\n\n")
                
                if not _chat_history:
                    f.write("(Chưa có hội thoại nào được ghi lại)\n")
                else:
                    for line in _chat_history:
                        f.write(line + '\n')
            
            print(f"✅ Đã lưu hội thoại vào file: {filename}")
        except Exception as e:
            print(f"❌ Lỗi khi lưu file: {e}")

def _patched_print(*args, **kwargs):
    """Hàm print thay thế để ghi lại mọi output của assistant"""
    global _chat_history, _original_print
    
    # Lấy nội dung cần in
    content = ' '.join(str(arg) for arg in args)
    
    # Ghi vào lịch sử (kèm thời gian, phân biệt assistant)
    timestamp = datetime.now().strftime('%H:%M:%S')
    _chat_history.append(f"[{timestamp}] 🤖 {content}")
    
    # Gọi hàm print gốc
    if _original_print:
        _original_print(*args, **kwargs)

def _wrap_process_command(assistant, original_method):
    """Wrapper cho process_command để ghi lại input của người dùng"""
    def wrapper(command: str) -> bool:
        global _chat_history
        
        # Lưu câu lệnh của user (trừ lệnh lưu hội thoại để tránh trùng)
        cmd_lower = command.strip().lower()
        if cmd_lower not in ['lưu hội thoại', 'save chat', 'lưu chat', 'save_conversation']:
            timestamp = datetime.now().strftime('%H:%M:%S')
            _chat_history.append(f"[{timestamp}] 👤 {command}")
        
        # Gọi phương thức gốc
        return original_method(command)
    return wrapper

def register(assistant: Any) -> None:
    """Đăng ký plugin vào assistant"""
    global _original_print, _original_process_command
    
    # 1. Thay thế hàm print để ghi lại output
    _original_print = print
    sys.modules['builtins'].print = _patched_print
    
    # 2. Bọc phương thức process_command để ghi lại input
    _original_process_command = assistant.process_command
    assistant.process_command = _wrap_process_command(assistant, _original_process_command)
    
    # 3. Thêm handler xử lý lệnh lưu hội thoại
    handler = SaveChatHandler()
    assistant.handlers.append(handler)
    
    # Thông báo plugin đã sẵn sàng (dùng print gốc để tránh ghi vào lịch sử)
    _original_print("✅ Plugin lưu hội thoại đã được kích hoạt. Gõ 'lưu hội thoại' để lưu chat.")

# Thông tin plugin bắt buộc
plugin_info = {
    "enabled": True,
    "register": register,
    "command_handle": ["lưu hội thoại", "save chat", "lưu chat", "save_conversation"]
}