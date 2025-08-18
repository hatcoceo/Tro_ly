import struct
import os
import json
DB_FILE = 'mydatabase.mydb'
PAGE_SIZE = 4096
HEADER_FORMAT = '8sIII'
MAGIC = b'MYDBFMT1'


class MiniBinaryDB:

    def __init__(self, file_path=DB_FILE):
        self.file_path = file_path
        self.tables = {}
        if not os.path.exists(file_path):
            self._init_db()
        else:
            self._load_metadata()

    def _init_db(self):
        with open(self.file_path, 'wb') as f:
            header = struct.pack(HEADER_FORMAT, MAGIC, PAGE_SIZE, 0, PAGE_SIZE)
            f.write(header)
            f.write(b'\x00' * (PAGE_SIZE - len(header)))
            f.write(b'\x00' * PAGE_SIZE)

    def _load_metadata(self):
        with open(self.file_path, 'rb') as f:
            header = f.read(struct.calcsize(HEADER_FORMAT))
            magic, page_size, table_count, metadata_offset = struct.unpack(
                HEADER_FORMAT, header)
            if magic != MAGIC:
                raise ValueError('File DB không hợp lệ!')
            f.seek(metadata_offset)
            raw = f.read(PAGE_SIZE)
            meta_str = raw.split(b'\x00', 1)[0].decode(errors='ignore').strip()
            if meta_str:
                try:
                    self.tables = json.loads(meta_str)
                except json.JSONDecodeError:
                    print('⚠️ Metadata bị hỏng, bỏ qua!')
                    self.tables = {}

    def _save_metadata(self):
        with open(self.file_path, 'r+b') as f:
            f.seek(PAGE_SIZE)
            meta_str = json.dumps(self.tables).encode()
            if len(meta_str) > PAGE_SIZE:
                raise ValueError('⚠️ Metadata quá lớn!')
            f.write(meta_str + b'\x00' * (PAGE_SIZE - len(meta_str)))

    def create_table(self, name, columns):
        if name in self.tables:
            print(f"Bảng '{name}' đã tồn tại!")
            return
        data_page_offset = (2 + len(self.tables)) * PAGE_SIZE
        self.tables[name] = {'columns': columns, 'page': data_page_offset}
        self._save_metadata()
        with open(self.file_path, 'ab') as f:
            f.write(b'\x00' * PAGE_SIZE)
        print(f"✅ Đã tạo bảng '{name}' với cột {columns}")

    def insert(self, name, values):
        if name not in self.tables:
            print(f"Bảng '{name}' không tồn tại!")
            return
        columns = self.tables[name]['columns']
        if len(values) != len(columns):
            print('❌ Số lượng giá trị không khớp số cột!')
            return
        record_data = json.dumps(values).encode()
        record_len = struct.pack('I', len(record_data))
        page_offset = self.tables[name]['page']
        with open(self.file_path, 'r+b') as f:
            f.seek(page_offset)
            old_data = f.read(PAGE_SIZE)
            used_data = old_data.rstrip(b'\x00')
            new_data = used_data + record_len + record_data
            if len(new_data) > PAGE_SIZE:
                print('❌ Page đầy, chưa hỗ trợ mở rộng!')
                return
            f.seek(page_offset)
            f.write(new_data + b'\x00' * (PAGE_SIZE - len(new_data)))
        print(f"✅ Đã thêm bản ghi vào '{name}': {values}")

    def select_all(self, name):
        if name not in self.tables:
            print(f"Bảng '{name}' không tồn tại!")
            return
        page_offset = self.tables[name]['page']
        with open(self.file_path, 'rb') as f:
            f.seek(page_offset)
            raw = f.read(PAGE_SIZE).rstrip(b'\x00')
        records = []
        pos = 0
        while pos < len(raw):
            if pos + 4 > len(raw):
                break
            rec_len = struct.unpack('I', raw[pos:pos + 4])[0]
            pos += 4
            rec_data = raw[pos:pos + rec_len]
            pos += rec_len
            try:
                records.append(json.loads(rec_data.decode()))
            except json.JSONDecodeError:
                print('⚠️ Bỏ qua bản ghi hỏng!')
        print(f"📋 Dữ liệu bảng '{name}':")
        for r in records:
            print(r)


class DBPluginHandler:

    def __init__(self):
        self.db = MiniBinaryDB()

    def can_handle(self, command: str) ->bool:
        cmd = command.lower()
        return cmd.startswith('create table') or cmd.startswith('insert into'
            ) or cmd.startswith('select * from')

    def handle(self, command: str):
        cmd = command.lower()
        if cmd.startswith('create table'):
            name_cols = command[len('create table'):].strip()
            name, cols_str = name_cols.split('(', 1)
            cols = [c.strip() for c in cols_str.strip(' )').split(',')]
            self.db.create_table(name.strip(), cols)
        elif cmd.startswith('insert into'):
            name_vals = command[len('insert into'):].strip()
            name, vals_str = name_vals.split('values', 1)
            vals = [v.strip().strip("'") for v in vals_str.strip(' ()').
                split(',')]
            self.db.insert(name.strip(), vals)
        elif cmd.startswith('select * from'):
            table_name = command[len('select * from'):].strip()
            self.db.select_all(table_name)


plugin_info = {'enabled': False, 'register': lambda assistant: assistant.
    handlers.append(DBPluginHandler()), 'command_handle': ['create table',
    'insert into', 'select * from']}
