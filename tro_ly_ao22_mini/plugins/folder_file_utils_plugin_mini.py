import os
import shutil
import glob
import zipfile
from typing import List, Dict, Any
from tabulate import tabulate
from datetime import datetime, timedelta
import filecmp
plugin_info = {'name': 'Folder & File Utility Library', 'version': '1.1',
    'enabled': False, 'register': lambda assistant:
    register_folder_file_utils(assistant)}


def register_folder_file_utils(assistant):
    assistant.context['folder_file_utils'] = FolderFileUtils()


class FolderFileUtils:

    def create_folder(self, path: str):
        os.makedirs(path, exist_ok=True)
        print(f'✅ Đã tạo thư mục: {path}')

    def delete_folder(self, path: str):
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f'🗑️ Đã xóa thư mục: {path}')
        else:
            print(f'⚠️ Thư mục không tồn tại: {path}')

    def copy_folder(self, src: str, dest: str):
        """Sao chép toàn bộ thư mục"""
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        print(f'📂 Đã sao chép thư mục {src} → {dest}')

    def list_folders(self, path: str) ->List[str]:
        return [f for f in os.listdir(path) if os.path.isdir(os.path.join(
            path, f))]

    def list_files(self, path: str, extension_filter: str=None) ->List[str]:
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join
            (path, f))]
        if extension_filter:
            files = [f for f in files if f.lower().endswith(
                extension_filter.lower())]
        return files

    def walk_directory(self, path: str) ->List[Dict[str, Any]]:
        file_list = []
        for root, dirs, files in os.walk(path):
            for name in files:
                full_path = os.path.join(root, name)
                stat = os.stat(full_path)
                file_list.append({'Tên': name, 'Đường dẫn': full_path,
                    'Kích thước (KB)': round(stat.st_size / 1024, 2),
                    'Ngày sửa đổi': datetime.fromtimestamp(stat.st_mtime).
                    strftime('%Y-%m-%d %H:%M:%S')})
        return file_list

    def get_folder_size(self, path: str) ->float:
        """Tính tổng dung lượng thư mục (KB)"""
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.isfile(fp):
                    total += os.path.getsize(fp)
        return round(total / 1024, 2)

    def copy_file(self, src: str, dest: str):
        shutil.copy2(src, dest)
        print(f'📄 Đã sao chép file từ {src} → {dest}')

    def move_file(self, src: str, dest: str):
        shutil.move(src, dest)
        print(f'📄 Đã di chuyển file từ {src} → {dest}')

    def delete_file(self, path: str):
        if os.path.exists(path):
            os.remove(path)
            print(f'🗑️ Đã xóa file: {path}')
        else:
            print(f'⚠️ File không tồn tại: {path}')

    def rename(self, old_path: str, new_path: str):
        os.rename(old_path, new_path)
        print(f'✏️ Đã đổi tên từ {old_path} → {new_path}')

    def read_file(self, path: str, encoding='utf-8') ->str:
        with open(path, 'r', encoding=encoding) as f:
            return f.read()

    def write_file(self, path: str, content: str, encoding='utf-8'):
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)
        print(f'✅ Đã ghi nội dung vào file: {path}')

    def append_file(self, path: str, content: str, encoding='utf-8'):
        with open(path, 'a', encoding=encoding) as f:
            f.write(content)
        print(f'📌 Đã thêm nội dung vào file: {path}')

    def find_files(self, directory: str, pattern: str) ->List[str]:
        return glob.glob(os.path.join(directory, pattern))

    def search_text_in_files(self, directory: str, text: str,
        extension_filter: str=None) ->List[str]:
        """Tìm chuỗi văn bản trong tất cả file (có thể lọc theo đuôi)"""
        matched_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if extension_filter and not file.lower().endswith(
                    extension_filter.lower()):
                    continue
                try:
                    with open(os.path.join(root, file), 'r', encoding=
                        'utf-8', errors='ignore') as f:
                        if text in f.read():
                            matched_files.append(os.path.join(root, file))
                except:
                    pass
        return matched_files

    def zip_folder(self, folder_path: str, zip_path: str):
        shutil.make_archive(zip_path.replace('.zip', ''), 'zip', folder_path)
        print(f'📦 Đã nén {folder_path} → {zip_path}')

    def unzip_file(self, zip_path: str, extract_to: str):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f'📂 Đã giải nén {zip_path} → {extract_to}')

    def sync_folders(self, src: str, dest: str):
        """Đồng bộ thư mục: copy file mới hoặc file khác nội dung"""
        for root, dirs, files in os.walk(src):
            rel_path = os.path.relpath(root, src)
            target_dir = os.path.join(dest, rel_path)
            os.makedirs(target_dir, exist_ok=True)
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(target_dir, file)
                if not os.path.exists(dest_file) or not filecmp.cmp(src_file,
                    dest_file, shallow=False):
                    shutil.copy2(src_file, dest_file)
                    print(f'🔄 Cập nhật: {src_file} → {dest_file}')

    def compare_folders(self, folder1: str, folder2: str) ->Dict[str, List[str]
        ]:
        """So sánh nội dung giữa 2 thư mục"""
        comparison = filecmp.dircmp(folder1, folder2)
        return {'only_in_folder1': comparison.left_only, 'only_in_folder2':
            comparison.right_only, 'diff_files': comparison.diff_files,
            'common_files': comparison.common_files}

    def delete_old_files(self, directory: str, days: int):
        """Xóa file cũ hơn X ngày"""
        cutoff = datetime.now() - timedelta(days=days)
        deleted = []
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if datetime.fromtimestamp(os.path.getmtime(file_path)
                    ) < cutoff:
                    os.remove(file_path)
                    deleted.append(file_path)
        print(f'🗑️ Đã xóa {len(deleted)} file cũ hơn {days} ngày')
        return deleted

    def print_directory_table(self, file_list: List[Dict[str, Any]]):
        if not file_list:
            print('⚠️ Không có dữ liệu.')
            return
        headers = file_list[0].keys()
        rows = [list(item.values()) for item in file_list]
        print(tabulate(rows, headers=headers, tablefmt='grid'))
