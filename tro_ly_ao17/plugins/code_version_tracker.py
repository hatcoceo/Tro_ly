import os
import hashlib
import datetime
import shutil

# Thư mục sẽ chứa các snapshot mã
SNAPSHOT_FOLDER = "code_snapshots"
# Tên file chính của dự án để giám sát
MAIN_FILE = "assistant76.py"  # <-- đổi thành tên file chính, ví dụ: main.py

def plugin_register(assistant):
    """
    Hàm register cho plugin, được gọi tự động bởi hệ thống assistant
    """
    ensure_folder(SNAPSHOT_FOLDER)
    track_code_changes(MAIN_FILE)

def ensure_folder(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"✅ Tạo thư mục: {folder}")

def get_file_hash(filepath):
    """
    Tính hash MD5 của file để biết có thay đổi hay không
    """
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5.hexdigest()

def track_code_changes(filepath):
    """
    So sánh hash file hiện tại với lần lưu cuối.
    Nếu khác, sao chép file vào thư mục snapshot.
    """
    hash_file = os.path.join(SNAPSHOT_FOLDER, "hash.txt")

    # Bước 1: tính hash hiện tại
    if not os.path.exists(filepath):
        print(f"⚠️ File {filepath} không tồn tại. Bỏ qua tracking.")
        return

    current_hash = get_file_hash(filepath)

    # Bước 2: đọc hash cũ
    last_hash = None
    if os.path.exists(hash_file):
        with open(hash_file, "r") as f:
            last_hash = f.read().strip()

    # Bước 3: nếu khác hash -> lưu snapshot
    if current_hash != last_hash:
        # Tạo tên snapshot với timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_filename = f"{os.path.splitext(os.path.basename(filepath))[0]}_{timestamp}.py"
        snapshot_path = os.path.join(SNAPSHOT_FOLDER, snapshot_filename)

        shutil.copy2(filepath, snapshot_path)
        print(f"💾 Code thay đổi. Đã lưu snapshot: {snapshot_path}")

        # Ghi lại hash mới
        with open(hash_file, "w") as f:
            f.write(current_hash)
    else:
        print(" 📢 Không có thay đổi trong mã. Không cần lưu snapshot.")

# Thông tin plugin
plugin_info = {
    "enabled": True,
    "register": plugin_register,
    "methods": [],
    "classes": [],
    "description": "Lưu trữ bản sao của mã chính phục vụ fallback"
}