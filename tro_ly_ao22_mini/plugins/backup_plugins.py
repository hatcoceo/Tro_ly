import os
import hashlib
import threading
import time
from datetime import datetime
import json
HASH_DB = 'backup_plugins/hash_db.json'


def hash_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()


class BackupPluginHandler:

    def __init__(self, assistant):
        self.plugins_folder = 'plugins'
        self.backup_folder = 'backup_plugins'
        os.makedirs(self.backup_folder, exist_ok=True)
        self.file_hashes = self.load_hash_db()
        self.check_changes_on_start()
        threading.Thread(target=self.watch_loop, daemon=True).start()

    def load_hash_db(self):
        if not os.path.exists(HASH_DB):
            return {}
        try:
            with open(HASH_DB, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def save_hash_db(self):
        with open(HASH_DB, 'w', encoding='utf-8') as f:
            json.dump(self.file_hashes, f, indent=4)

    def check_changes_on_start(self):
        """Kiểm tra thay đổi khi trợ lý vừa khởi động"""
        for filename in os.listdir(self.plugins_folder):
            if not filename.endswith('.py') or filename.startswith('_'):
                continue
            path = os.path.join(self.plugins_folder, filename)
            new_hash = hash_file(path)
            old_hash = self.file_hashes.get(filename)
            if old_hash is None:
                print(f'📄 Phát hiện plugin mới: {filename}')
                self.backup_file(filename, path)
                self.file_hashes[filename] = new_hash
                continue
            if new_hash != old_hash:
                print(f'⚠️ Plugin đã thay đổi từ lần chạy trước: {filename}')
                self.backup_file(filename, path)
                self.file_hashes[filename] = new_hash
        self.save_hash_db()

    def watch_loop(self):
        """Theo dõi thay đổi khi trợ lý đang chạy"""
        while True:
            try:
                for filename in os.listdir(self.plugins_folder):
                    if not filename.endswith('.py') or filename.startswith('_'
                        ):
                        continue
                    path = os.path.join(self.plugins_folder, filename)
                    new_hash = hash_file(path)
                    old_hash = self.file_hashes.get(filename)
                    if old_hash and new_hash == old_hash:
                        continue
                    if old_hash is None:
                        print(f'📄 Phát hiện plugin mới: {filename}')
                    else:
                        print(f'⚠️ Plugin thay đổi trong lúc chạy: {filename}')
                    self.backup_file(filename, path)
                    self.file_hashes[filename] = new_hash
                    self.save_hash_db()
                time.sleep(1)
            except Exception as e:
                print('⚠️ WATCH ERROR:', e)

    def backup_file(self, filename, path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        plugin_name = filename[:-3]
        save_dir = os.path.join(self.backup_folder, plugin_name)
        os.makedirs(save_dir, exist_ok=True)
        dest = os.path.join(save_dir, f'{timestamp}.py')
        with open(path, 'rb') as src, open(dest, 'wb') as dst:
            dst.write(src.read())
        print(f'💾 Sao lưu: {dest}')


def register(assistant):
    assistant.handlers.append(BackupPluginHandler(assistant))


plugin_info = {'enabled': True, 'register': register}
