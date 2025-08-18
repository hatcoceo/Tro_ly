"""
#sd
CREATE TABLE users
INSERT INTO users (name,age) VALUES ('Alice',25)
INSERT INTO users (name,age) VALUES ('Bob',30)
INSERT INTO users (name,age) VALUES ('Charlie',20)

-- Sắp xếp và giới hạn
SELECT * FROM users ORDER BY age DESC LIMIT 2

-- Cập nhật dữ liệu
UPDATE users SET age=26 WHERE name='Alice'

-- Lọc + sắp xếp
SELECT name,age FROM users WHERE age>20 ORDER BY name ASC

-- Xóa dữ liệu
DELETE FROM users WHERE age<25

-- xem toàn bộ bảng 
SELECT * FROM users

-- xóa toàn bộ dữ liệu trong bảng( còn tên bảng )
DELETE FROM users

-- xóa cả bảng ( cả tên bảng)
DROP TABLE users2
"""
import json
import os
import re


class SQLDatabase:

    def __init__(self, db_file='sql_db.json'):
        self.db_file = db_file
        if not os.path.exists(db_file):
            with open(db_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)

    def _read_db(self):
        with open(self.db_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _write_db(self, data):
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def create_table(self, table):
        db = self._read_db()
        if table not in db:
            db[table] = []
            self._write_db(db)
            return f'✅ Created table {table}'
        return f"⚠️ Table '{table}' already exists"

    def drop_table(self, table):
        db = self._read_db()
        if table in db:
            del db[table]
            self._write_db(db)
            return f'🗑 Dropped table {table}'
        return f"⚠️ Table '{table}' not found"

    def insert(self, table, columns, values):
        db = self._read_db()
        if table not in db:
            return f"⚠️ Table '{table}' not found"
        record = dict(zip(columns, values))
        db[table].append(record)
        self._write_db(db)
        return f'✅ Inserted into {table}: {record}'

    def select(self, table, columns='*', where=None, order_by=None, limit=None
        ):
        db = self._read_db()
        if table not in db:
            return f"⚠️ Table '{table}' not found"
        rows = db[table]
        if where:
            key, op, val = where
            if op == '=':
                rows = [r for r in rows if str(r.get(key)) == val]
            elif op == '!=':
                rows = [r for r in rows if str(r.get(key)) != val]
            elif op == '>':
                rows = [r for r in rows if str(r.get(key)).isdigit() and 
                    int(r.get(key)) > int(val)]
            elif op == '<':
                rows = [r for r in rows if str(r.get(key)).isdigit() and 
                    int(r.get(key)) < int(val)]
            elif op.upper() == 'LIKE':
                rows = [r for r in rows if val.lower() in str(r.get(key, ''
                    )).lower()]
        if order_by:
            col, direction = order_by
            rows.sort(key=lambda r: r.get(col), reverse=direction == 'DESC')
        if columns != '*':
            rows = [{col: r.get(col) for col in columns} for r in rows]
        if limit is not None:
            rows = rows[:limit]
        return rows if rows else '📭 No data found'

    def update(self, table, updates, where=None):
        db = self._read_db()
        if table not in db:
            return f"⚠️ Table '{table}' not found"
        count = 0
        for row in db[table]:
            if where:
                key, op, val = where
                match = False
                if op == '=':
                    match = str(row.get(key)) == val
                elif op == '!=':
                    match = str(row.get(key)) != val
                elif op == '>':
                    match = str(row.get(key)).isdigit() and int(row.get(key)
                        ) > int(val)
                elif op == '<':
                    match = str(row.get(key)).isdigit() and int(row.get(key)
                        ) < int(val)
                elif op.upper() == 'LIKE':
                    match = val.lower() in str(row.get(key, '')).lower()
                if not match:
                    continue
            row.update(updates)
            count += 1
        self._write_db(db)
        return f'✏️ Updated {count} rows'

    def delete(self, table, where=None):
        db = self._read_db()
        if table not in db:
            return f"⚠️ Table '{table}' not found"
        before = len(db[table])
        if where:
            key, op, val = where
            if op == '=':
                db[table] = [r for r in db[table] if str(r.get(key)) != val]
            elif op == '!=':
                db[table] = [r for r in db[table] if str(r.get(key)) == val]
            elif op == '>':
                db[table] = [r for r in db[table] if not (str(r.get(key)).
                    isdigit() and int(r.get(key)) > int(val))]
            elif op == '<':
                db[table] = [r for r in db[table] if not (str(r.get(key)).
                    isdigit() and int(r.get(key)) < int(val))]
            elif op.upper() == 'LIKE':
                db[table] = [r for r in db[table] if val.lower() not in str
                    (r.get(key, '')).lower()]
        else:
            db[table] = []
        self._write_db(db)
        return f'🗑 Deleted {before - len(db[table])} rows'


class SQLHandler:

    def __init__(self, assistant):
        self.assistant = assistant
        self.db = SQLDatabase()

    def can_handle(self, command: str) ->bool:
        return bool(re.match(
            '(?i)^(CREATE|DROP|INSERT|SELECT|DELETE|UPDATE)\\s', command.
            strip()))

    def handle(self, command: str):
        sql = command.strip()
        cmd = sql.split()[0].upper()
        try:
            if cmd == 'CREATE':
                table = sql.split()[2]
                print(self.db.create_table(table))
            elif cmd == 'DROP':
                table = sql.split()[2]
                print(self.db.drop_table(table))
            elif cmd == 'INSERT':
                match = re.match(
                    'INSERT\\s+INTO\\s+(\\w+)\\s*\\((.*?)\\)\\s*VALUES\\s*\\((.*?)\\)'
                    , sql, re.I)
                if match:
                    table = match.group(1)
                    columns = [c.strip() for c in match.group(2).split(',')]
                    values = [v.strip().strip('\'"') for v in match.group(3
                        ).split(',')]
                    print(self.db.insert(table, columns, values))
                else:
                    print('⚠️ Invalid INSERT syntax')
            elif cmd == 'SELECT':
                match = re.match(
                    'SELECT\\s+(.*?)\\s+FROM\\s+(\\w+)(?:\\s+WHERE\\s+(.*?))?(?:\\s+ORDER\\s+BY\\s+(\\w+)\\s*(ASC|DESC)?)?(?:\\s+LIMIT\\s+(\\d+))?$'
                    , sql, re.I)
                if match:
                    columns = match.group(1)
                    table = match.group(2)
                    where_clause = match.group(3)
                    order_col = match.group(4)
                    order_dir = match.group(5) or 'ASC'
                    limit = match.group(6)
                    where = None
                    if where_clause:
                        w_match = re.match(
                            "(\\w+)\\s*(=|!=|>|<|LIKE)\\s*'?(.*?)'?$",
                            where_clause, re.I)
                        if w_match:
                            where = w_match.group(1), w_match.group(2
                                ), w_match.group(3)
                    if columns != '*':
                        columns = [c.strip() for c in columns.split(',')]
                    else:
                        columns = '*'
                    order_by = (order_col, order_dir.upper()
                        ) if order_col else None
                    limit = int(limit) if limit else None
                    print(self.db.select(table, columns, where, order_by,
                        limit))
                else:
                    print('⚠️ Invalid SELECT syntax')
            elif cmd == 'UPDATE':
                match = re.match(
                    'UPDATE\\s+(\\w+)\\s+SET\\s+(.*?)\\s*(?:WHERE\\s+(.*))?$',
                    sql, re.I)
                if match:
                    table = match.group(1)
                    set_clause = match.group(2)
                    where_clause = match.group(3)
                    updates = {}
                    for pair in set_clause.split(','):
                        k, v = pair.split('=')
                        updates[k.strip()] = v.strip().strip('\'"')
                    where = None
                    if where_clause:
                        w_match = re.match(
                            "(\\w+)\\s*(=|!=|>|<|LIKE)\\s*'?(.*?)'?$",
                            where_clause, re.I)
                        if w_match:
                            where = w_match.group(1), w_match.group(2
                                ), w_match.group(3)
                    print(self.db.update(table, updates, where))
                else:
                    print('⚠️ Invalid UPDATE syntax')
            elif cmd == 'DELETE':
                match = re.match(
                    'DELETE\\s+FROM\\s+(\\w+)(?:\\s+WHERE\\s+(.*))?', sql, re.I
                    )
                if match:
                    table = match.group(1)
                    where_clause = match.group(2)
                    where = None
                    if where_clause:
                        w_match = re.match(
                            "(\\w+)\\s*(=|!=|>|<|LIKE)\\s*'?(.*?)'?$",
                            where_clause, re.I)
                        if w_match:
                            where = w_match.group(1), w_match.group(2
                                ), w_match.group(3)
                    print(self.db.delete(table, where))
                else:
                    print('⚠️ Invalid DELETE syntax')
        except Exception as e:
            print(f'⚠️ Error: {e}')


def register(assistant):
    handler = SQLHandler(assistant)
    assistant.handlers.append(handler)
    assistant.context['sql_db'] = handler.db


plugin_info = {'enabled': False, 'register': register, 'command_handle': [
    'SQL']}
