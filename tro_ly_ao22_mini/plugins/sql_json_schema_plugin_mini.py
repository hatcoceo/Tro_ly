"""
CREATE TABLE users (id INT, name TEXT)
CREATE TABLE orders (id INT, user_id INT, product TEXT)

INSERT INTO users (id, name) VALUES (1, 'Alice')
INSERT INTO users (id, name) VALUES (2, 'Bob')

INSERT INTO orders (id, user_id, product) VALUES (101, 1, 'Laptop')
INSERT INTO orders (id, user_id, product) VALUES (102, 1, 'Phone')
INSERT INTO orders (id, user_id, product) VALUES (103, 2, 'Tablet')

-- INNER JOIN
SELECT * FROM users INNER JOIN orders ON users.id = orders.user_id

-- LEFT JOIN
SELECT * FROM users LEFT JOIN orders ON users.id = orders.user_id

-- RIGHT JOIN
SELECT * FROM users RIGHT JOIN orders ON users.id = orders.user_id
"""
import json
import os
import re
from typing import Dict, List, Any


class SQLDatabaseWithSchema:

    def __init__(self, db_file='sql_db_schema.json'):
        self.db_file = db_file
        if not os.path.exists(db_file):
            with open(db_file, 'w', encoding='utf-8') as f:
                json.dump({'_schema': {}}, f, ensure_ascii=False, indent=4)

    def _read_db(self):
        with open(self.db_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _write_db(self, data):
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def create_table(self, table: str, columns: Dict[str, str]):
        db = self._read_db()
        if table in db:
            return f"⚠️ Table '{table}' already exists"
        db[table] = []
        db['_schema'][table] = columns
        self._write_db(db)
        return f'✅ Created table {table} with columns {columns}'

    def drop_table(self, table: str):
        db = self._read_db()
        if table not in db:
            return f"⚠️ Table '{table}' not found"
        del db[table]
        if table in db['_schema']:
            del db['_schema'][table]
        self._write_db(db)
        return f'🗑 Dropped table {table}'

    def insert(self, table: str, columns: List[str], values: List[str]):
        db = self._read_db()
        if table not in db:
            return f"⚠️ Table '{table}' not found"
        if table not in db['_schema']:
            return f"⚠️ No schema found for '{table}'"
        schema = db['_schema'][table]
        for col in columns:
            if col not in schema:
                return f"⚠️ Column '{col}' not in schema of '{table}'"
        record = {}
        for col, val in zip(columns, values):
            dtype = schema[col]
            try:
                if dtype == 'INT':
                    record[col] = int(val)
                elif dtype == 'FLOAT':
                    record[col] = float(val)
                else:
                    record[col] = str(val)
            except ValueError:
                return (
                    f"⚠️ Value '{val}' is not valid for column '{col}' ({dtype})"
                    )
        for col in schema:
            if col not in record:
                record[col] = None
        db[table].append(record)
        self._write_db(db)
        return f'✅ Inserted into {table}: {record}'

    def select(self, sql: str):
        db = self._read_db()
        join_match = re.search(
            'SELECT\\s+(.*?)\\s+FROM\\s+(\\w+)\\s+(INNER|LEFT|RIGHT)\\s+JOIN\\s+(\\w+)\\s+ON\\s+(\\w+)\\.(\\w+)\\s*=\\s*(\\w+)\\.(\\w+)'
            , sql, re.I)
        if join_match:
            select_cols = join_match.group(1).strip()
            table1 = join_match.group(2)
            join_type = join_match.group(3).upper()
            table2 = join_match.group(4)
            on_table1 = join_match.group(5)
            on_col1 = join_match.group(6)
            on_table2 = join_match.group(7)
            on_col2 = join_match.group(8)
            if table1 not in db or table2 not in db:
                return f'⚠️ One or both tables not found'
            rows1 = db[table1]
            rows2 = db[table2]
            result = []
            if join_type == 'INNER':
                for r1 in rows1:
                    for r2 in rows2:
                        if r1[on_col1] == r2[on_col2]:
                            result.append({**{f'{table1}.{k}': v for k, v in
                                r1.items()}, **{f'{table2}.{k}': v for k, v in
                                r2.items()}})
            elif join_type == 'LEFT':
                for r1 in rows1:
                    matched = False
                    for r2 in rows2:
                        if r1[on_col1] == r2[on_col2]:
                            result.append({**{f'{table1}.{k}': v for k, v in
                                r1.items()}, **{f'{table2}.{k}': v for k, v in
                                r2.items()}})
                            matched = True
                    if not matched:
                        result.append({**{f'{table1}.{k}': v for k, v in r1
                            .items()}, **{f'{table2}.{k}': None for k in db
                            ['_schema'][table2].keys()}})
            elif join_type == 'RIGHT':
                for r2 in rows2:
                    matched = False
                    for r1 in rows1:
                        if r1[on_col1] == r2[on_col2]:
                            result.append({**{f'{table1}.{k}': v for k, v in
                                r1.items()}, **{f'{table2}.{k}': v for k, v in
                                r2.items()}})
                            matched = True
                    if not matched:
                        result.append({**{f'{table1}.{k}': None for k in db
                            ['_schema'][table1].keys()}, **{f'{table2}.{k}':
                            v for k, v in r2.items()}})
            if select_cols == '*':
                return result
            else:
                cols = [c.strip() for c in select_cols.split(',')]
                return [{col: row.get(col) for col in cols} for row in result]
        match = re.match('SELECT\\s+\\*\\s+FROM\\s+(\\w+)', sql, re.I)
        if match:
            table = match.group(1)
            if table not in db:
                return f"⚠️ Table '{table}' not found"
            return db[table]
        return f'⚠️ Unsupported SELECT syntax'


class SQLSchemaHandler:

    def __init__(self, assistant):
        self.assistant = assistant
        self.db = SQLDatabaseWithSchema()

    def can_handle(self, command: str) ->bool:
        return bool(re.match('(?i)^(CREATE|DROP|INSERT|SELECT)\\s', command
            .strip()))

    def handle(self, command: str):
        sql = command.strip()
        cmd = sql.split()[0].upper()
        try:
            if cmd == 'CREATE':
                match = re.match('CREATE\\s+TABLE\\s+(\\w+)\\s*\\((.*?)\\)',
                    sql, re.I)
                if match:
                    table = match.group(1)
                    cols_str = match.group(2)
                    columns = {}
                    for col_def in cols_str.split(','):
                        col_name, col_type = col_def.strip().split()
                        columns[col_name] = col_type.upper()
                    print(self.db.create_table(table, columns))
                else:
                    print('⚠️ Invalid CREATE TABLE syntax')
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
                result = self.db.select(sql)
                print(result)
        except Exception as e:
            print(f'⚠️ Error: {e}')


def register(assistant):
    handler = SQLSchemaHandler(assistant)
    assistant.handlers.append(handler)
    assistant.context['sql_schema_db'] = handler.db


plugin_info = {'enabled': False, 'register': register, 'command_handle': [
    'SQL_SCHEMA']}
