"""
Nhập thư mục nguồn để đồng bộ: source_folder
Nhập thư mục đích: backup_folder
Nhập chuỗi cần tìm trong file: search_text
Nhập đuôi file để lọc (hoặc bỏ trống): .txt
Nhập thư mục cần nén: folder_to_zip
Nhập tên file zip: zipped_folder.zip
Nhập thư mục để giải nén: extract_here
"""
import os
from typing import Any, Dict, List
plugin_info = {'name': 'Quản Lý & Test Nâng Cao FolderFileUtils', 'version':
    '1.0', 'enabled': False, 'register': lambda assistant: register(assistant)}


class FolderFileHandler:

    def __init__(self, assistant):
        self.assistant = assistant

    def can_handle(self, command: str) ->bool:
        cmd = command.strip().lower()
        return cmd.startswith('quản lý file') or cmd.startswith(
            'test file advanced')

    def handle(self, command: str):
        folder_utils = self.assistant.context.get('folder_file_utils')
        if not folder_utils:
            print('❌ FolderFileUtils chưa được nạp!')
            return
        cmd = command.strip().lower()
        if cmd.startswith('quản lý file'):
            folder_name = input('Nhập tên thư mục muốn tạo: ')
            folder_utils.create_folder(folder_name)
            file_name = input('Nhập tên file muốn tạo: ')
            content = input('Nhập nội dung file: ')
            file_path = os.path.join(folder_name, file_name)
            folder_utils.write_file(file_path, content)
            files = folder_utils.list_files(folder_name)
            print('📂 Danh sách file trong thư mục:')
            for f in files:
                print('-', f)
            size_kb = folder_utils.get_folder_size(folder_name)
            print(f"📏 Dung lượng thư mục '{folder_name}': {size_kb} KB")
            old_folder = input('Nhập thư mục cần dọn file cũ: ')
            days = int(input('Nhập số ngày để xóa file cũ hơn: '))
            deleted_files = folder_utils.delete_old_files(old_folder, days)
            if deleted_files:
                print('🗑️ Đã xóa các file sau:')
                for f in deleted_files:
                    print('-', f)
            else:
                print('✅ Không có file nào cần xóa.')
        elif cmd.startswith('test file advanced'):
            src = input('Nhập thư mục nguồn để đồng bộ: ')
            dest = input('Nhập thư mục đích: ')
            folder_utils.sync_folders(src, dest)
            comparison = folder_utils.compare_folders(src, dest)
            print('\n📊 So sánh thư mục:')
            print('Chỉ có ở nguồn:', comparison['only_in_folder1'])
            print('Chỉ có ở đích:', comparison['only_in_folder2'])
            print('File khác nhau:', comparison['diff_files'])
            print('File giống nhau:', comparison['common_files'])
            text = input('Nhập chuỗi cần tìm trong file: ')
            ext_filter = input('Nhập đuôi file để lọc (hoặc bỏ trống): ')
            found_files = folder_utils.search_text_in_files(src, text, 
                ext_filter if ext_filter else None)
            print('\n🔍 Kết quả tìm kiếm:')
            for f in found_files:
                print('-', f)
            folder_to_zip = input('Nhập thư mục cần nén: ')
            zip_name = input('Nhập tên file zip: ')
            folder_utils.zip_folder(folder_to_zip, zip_name)
            extract_path = input('Nhập thư mục để giải nén: ')
            folder_utils.unzip_file(zip_name, extract_path)


def register(assistant):
    assistant.handlers.insert(1, FolderFileHandler(assistant))
    print("📥 Plugin 'quan_ly_test_folder_file_utils' đã được đăng ký.")
