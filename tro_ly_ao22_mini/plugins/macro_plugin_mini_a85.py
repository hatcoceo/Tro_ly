# sửa lỗi hàm thực thi ngay khi định nghe mà không chờ gọi ( call)
import os
import sys
import time
import builtins

macro_folder = 'macros'
os.makedirs(macro_folder, exist_ok=True)
recorder_is_playing = False


class MacroRecorder:
    def __init__(self):
        self.recording = False
        self.commands = []
        self.current_macro_name = None

    def start(self, macro_name):
        if self.recording:
            print(f"⚠️ Đang ghi macro '{self.current_macro_name}'. Dừng lại trước.")
            return
        self.recording = True
        self.commands = []
        self.current_macro_name = macro_name
        print(f'🔴 Bắt đầu ghi macro: {macro_name}')

    def stop(self):
        if not self.recording:
            print('⚠️ Không có macro nào đang được ghi.')
            return
        path = os.path.join(macro_folder, f'{self.current_macro_name}.txt')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.commands))
        print(f'🟢 Đã lưu macro ({len(self.commands)} lệnh) vào: {path}')
        self.recording = False
        self.commands = []
        self.current_macro_name = None

    def record(self, command: str):
        if self.recording and not recorder_is_playing and command.strip() and not command.startswith(('ghi macro ', 'dừng ghi macro', 'chạy macro ')):
            self.commands.append(command.strip())


recorder = MacroRecorder()


class MacroCommandHandler:
    def __init__(self, assistant):
        self.assistant = assistant
        self._original_input = sys.stdin
        self._install_input_hook()

    def _install_input_hook(self):
        class MacroInputWrapper:
            def __init__(self, original):
                self.original = original
            def readline(self):
                user_input = self.original.readline()
                recorder.record(user_input)
                return user_input
        sys.stdin = MacroInputWrapper(sys.stdin)

    def can_handle(self, command: str) -> bool:
        return command.startswith(('ghi macro ', 'dừng ghi macro', 'chạy macro '))

    def handle(self, command: str) -> bool:
        if command.startswith('ghi macro '):
            recorder.start(command[10:].strip())
            return True
        elif command == 'dừng ghi macro':
            recorder.stop()
            return True
        elif command.startswith('chạy macro '):
            rest = command[11:].strip()
            if not rest:
                print('❌ Thiếu tên macro.')
                return True
            delay = 1.0
            macro_name = rest
            if ' ' in rest:
                try:
                    possible_delay = rest.split()[-1]
                    delay = float(possible_delay)
                    macro_name = rest[:rest.rfind(possible_delay)].strip()
                except ValueError:
                    delay = 1.0
            self._play_macro(macro_name, delay)
            return True
        return False

    # ------------------ Hàm thay thế biến ------------------
    def _replace_vars(self, text, variables):
        for key, val in variables.items():
            text = text.replace(f'{{{key}}}', str(val))
        return text

    # ------------------ Xử lý một dòng lệnh đơn ------------------
    def _execute_line(self, line: str, variables: dict, auto_input_queue: list, original_input):
        line = line.strip()
        if not line:
            return False

        # INPUT value
        if line.startswith('INPUT '):
            value = line[6:].strip()
            value = self._replace_vars(value, variables)
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            auto_input_queue.append(value)
            return False

        # SET var = value
        if line.startswith('SET '):
            parts = line[4:].split('=', 1)
            if len(parts) == 2:
                var_name = parts[0].strip()
                var_value = parts[1].strip()
                var_value = self._replace_vars(var_value, variables)
                if (var_value.startswith('"') and var_value.endswith('"')) or (var_value.startswith("'") and var_value.endswith("'")):
                    var_value = var_value[1:-1]
                variables[var_name] = var_value
            return False

        # ? hỏi đáp (có thể có auto:)
        if line.startswith('? '):
            rest = line[2:].strip()
            auto_answer = None
            if ' auto:' in rest:
                parts = rest.split(' auto:', 1)
                question = parts[0].strip()
                auto_answer = parts[1].strip()
                question = self._replace_vars(question, variables)
                auto_answer = self._replace_vars(auto_answer, variables)
                if (auto_answer.startswith('"') and auto_answer.endswith('"')) or (auto_answer.startswith("'") and auto_answer.endswith("'")):
                    auto_answer = auto_answer[1:-1]
                try:
                    auto_answer = auto_answer.format(**variables)
                except KeyError:
                    pass
            else:
                question = self._replace_vars(rest, variables)
                auto_answer = None

            if auto_answer is not None:
                user_input = auto_answer
                print(f'🤖 (tự động) {question}\n👉 {user_input}')
            else:
                user_input = original_input(f'\n🤖 {question}\n👉 ')
            variables['answer'] = user_input
            print()
            return False

        # PRINT message
        if line.startswith('PRINT '):
            msg = line[6:].strip()
            msg = self._replace_vars(msg, variables)
            if (msg.startswith('"') and msg.endswith('"')) or (msg.startswith("'") and msg.endswith("'")):
                msg = msg[1:-1]
            print(f'📢 {msg}')
            return False

        # RETURN value
        if line.startswith('RETURN '):
            ret_value = line[7:].strip()
            ret_value = self._replace_vars(ret_value, variables)
            if (ret_value.startswith('"') and ret_value.endswith('"')) or (ret_value.startswith("'") and ret_value.endswith("'")):
                ret_value = ret_value[1:-1]
            return ret_value

        # Lệnh thường: gửi đến assistant
        cmd = self._replace_vars(line, variables)
        print(f'⏩ {cmd}')
        self.assistant.process_command(cmd)
        return False

    # ------------------ Đánh giá điều kiện IF ------------------
    def _eval_condition(self, cond, variables):
        cond = self._replace_vars(cond, variables).strip()
        for op in ['==', '!=', '>=', '<=', '>', '<']:
            if op in cond:
                left, right = cond.split(op, 1)
                left = left.strip()
                right = right.strip()
                # Bỏ dấu ngoặc kép nếu có
                if (left.startswith('"') and left.endswith('"')) or (left.startswith("'") and left.endswith("'")):
                    left = left[1:-1]
                if (right.startswith('"') and right.endswith('"')) or (right.startswith("'") and right.endswith("'")):
                    right = right[1:-1]
                # Thử chuyển sang số
                try:
                    left = int(left) if left.isdigit() else float(left)
                except ValueError:
                    pass
                try:
                    right = int(right) if right.isdigit() else float(right)
                except ValueError:
                    pass
                if op == '==': return left == right
                if op == '!=': return left != right
                if op == '>': return left > right
                if op == '<': return left < right
                if op == '>=': return left >= right
                if op == '<=': return left <= right
        # Nếu không có toán tử, coi như kiểm tra truthy
        return bool(cond) and cond.lower() not in ('false', '0', '')

    # ------------------ Chạy macro với đầy đủ cấu trúc ------------------
    def _play_macro(self, macro_name, delay=1.0):
        global recorder_is_playing
        path = os.path.join(macro_folder, f'{macro_name}.txt')
        if not os.path.exists(path):
            print(f'❌ Không tìm thấy macro: {macro_name}')
            return

        print(f'🏃 Đang chạy macro: {macro_name} (delay: {delay:.1f}s)')
        recorder_is_playing = True

        with open(path, 'r', encoding='utf-8') as f:
            raw_lines = [line.rstrip('\n') for line in f]

        # ---- Bước 1: quét định nghĩa hàm (FUNCTION ... ENDFUNCTION) ----
        functions = {}
        i = 0
        while i < len(raw_lines):
            line = raw_lines[i].strip()
            if line.startswith('FUNCTION '):
                func_name = line[9:].strip()
                start = i
                nested = 1
                j = i + 1
                while j < len(raw_lines):
                    l = raw_lines[j].strip()
                    if l.startswith('FUNCTION '):
                        nested += 1
                    elif l == 'ENDFUNCTION':
                        nested -= 1
                        if nested == 0:
                            break
                    j += 1
                # Lưu vị trí bắt đầu và kết thúc (chỉ lưu dòng đầu và dòng cuối)
                functions[func_name] = (start + 1, j - 1)
                i = j + 1
            else:
                i += 1

        # ---- Bước 2: thực thi macro, bỏ qua các khối FUNCTION ----
        variables = {}
        auto_input_queue = []
        original_input = builtins.input

        # Các ngăn xếp cho cấu trúc điều khiển
        loop_stack = []          # (start_line, remaining_count)
        foreach_stack = []       # (start_line, items, current_index, var_name)
        if_stack = []            # (start_line, has_else, skip_block)
        call_stack = []          # (return_line, variables_backup)

        def auto_input(prompt=''):
            if auto_input_queue:
                answer = auto_input_queue.pop(0)
                print(f'{prompt}{answer}')
                return answer
            else:
                return original_input(prompt)

        try:
            builtins.input = auto_input
            i = 0
            while i < len(raw_lines):
                line = raw_lines[i].strip()
                if not line:
                    i += 1
                    continue

                # ----- Bỏ qua toàn bộ khối FUNCTION -----
                if line.startswith('FUNCTION '):
                    # Nhảy đến ENDFUNCTION tương ứng
                    nested = 1
                    j = i + 1
                    while j < len(raw_lines):
                        l = raw_lines[j].strip()
                        if l.startswith('FUNCTION '):
                            nested += 1
                        elif l == 'ENDFUNCTION':
                            nested -= 1
                            if nested == 0:
                                break
                        j += 1
                    i = j + 1
                    continue

                if line == 'ENDFUNCTION':
                    # Nếu gặp ENDFUNCTION lẻ (do lỗi cú pháp) thì bỏ qua
                    i += 1
                    continue

                # ----- CALL function -----
                if line.startswith('CALL '):
                    rest = line[5:].strip()
                    store_var = None
                    if ' -> ' in rest:
                        parts = rest.split(' -> ', 1)
                        func_part = parts[0].strip()
                        store_var = parts[1].strip()
                    else:
                        func_part = rest
                    func_name = func_part
                    if func_name not in functions:
                        print(f'❌ Hàm không tồn tại: {func_name}')
                        i += 1
                        continue
                    start_line, end_line = functions[func_name]
                    # Lưu ngữ cảnh hiện tại (dòng quay lại và biến)
                    call_stack.append((i + 1, variables.copy()))
                    # Tạo biến cục bộ mới cho hàm (có thể kế thừa hoặc không, ở đây dùng bản sao)
                    func_vars = {}
                    # Chạy các dòng trong hàm
                    j = start_line
                    ret_value = None
                    while j <= end_line:
                        sub_line = raw_lines[j].strip()
                        if sub_line.startswith('RETURN '):
                            ret_value = self._execute_line(sub_line, func_vars, auto_input_queue, original_input)
                            if ret_value is False:
                                ret_value = None
                            break
                        else:
                            self._execute_line(sub_line, func_vars, auto_input_queue, original_input)
                            time.sleep(delay)
                        j += 1
                    # Khôi phục ngữ cảnh
                    return_line, prev_vars = call_stack.pop()
                    variables = prev_vars
                    if store_var and ret_value is not None:
                        variables[store_var] = ret_value
                    i = return_line
                    continue

                # ----- IF / ELSE / ENDIF -----
                if line.startswith('IF '):
                    condition = line[3:].strip()
                    result = self._eval_condition(condition, variables)
                    # Tìm ENDIF và ELSE tương ứng
                    nested = 1
                    j = i + 1
                    else_line = None
                    while j < len(raw_lines):
                        l = raw_lines[j].strip()
                        if l.startswith('IF '):
                            nested += 1
                        elif l == 'ENDIF':
                            nested -= 1
                            if nested == 0:
                                break
                        elif l == 'ELSE' and nested == 1:
                            else_line = j
                        j += 1
                    if result:
                        # Thực hiện if-block
                        if_stack.append((i, else_line is not None, False))
                        i += 1
                    else:
                        if else_line is not None:
                            i = else_line + 1
                            if_stack.append((i, True, True))
                        else:
                            i = j + 1
                    continue

                if line == 'ELSE':
                    if not if_stack:
                        print('❌ Lỗi: ELSE không có IF')
                        i += 1
                        continue
                    start_line, has_else, in_else = if_stack[-1]
                    if in_else:
                        print('❌ Lỗi: ELSE lồng nhau')
                        i += 1
                        continue
                    # Nhảy đến sau ENDIF
                    nested = 1
                    j = i + 1
                    while j < len(raw_lines):
                        l = raw_lines[j].strip()
                        if l.startswith('IF '):
                            nested += 1
                        elif l == 'ENDIF':
                            nested -= 1
                            if nested == 0:
                                break
                        j += 1
                    i = j + 1
                    if_stack.pop()
                    continue

                if line == 'ENDIF':
                    if if_stack:
                        if_stack.pop()
                    i += 1
                    continue

                # ----- LOOP -----
                if line.startswith('LOOP '):
                    count_part = line[5:].strip()
                    count_part = self._replace_vars(count_part, variables)
                    try:
                        count = int(count_part)
                    except ValueError:
                        print(f'❌ Lỗi: Số lần lặp không hợp lệ: {count_part}')
                        i += 1
                        continue
                    if count <= 0:
                        # Bỏ qua khối LOOP
                        nested = 1
                        j = i + 1
                        while j < len(raw_lines):
                            l = raw_lines[j].strip()
                            if l.startswith('LOOP '):
                                nested += 1
                            elif l == 'ENDLOOP':
                                nested -= 1
                                if nested == 0:
                                    break
                            j += 1
                        i = j + 1
                        continue
                    loop_stack.append((i, count))
                    i += 1
                    continue

                if line == 'ENDLOOP':
                    if not loop_stack:
                        print('❌ Lỗi: ENDLOOP không có LOOP')
                        i += 1
                        continue
                    start_line, remaining = loop_stack.pop()
                    remaining -= 1
                    if remaining > 0:
                        loop_stack.append((start_line, remaining))
                        i = start_line + 1
                    else:
                        i += 1
                    continue

                # ----- FOREACH -----
                if line.startswith('FOREACH '):
                    rest = line[8:].strip()
                    if ' IN ' not in rest:
                        print(f'❌ Lỗi cú pháp FOREACH: {line}')
                        i += 1
                        continue
                    var_part, list_part = rest.split(' IN ', 1)
                    var_name = var_part.strip()
                    list_expr = list_part.strip()
                    list_expr = self._replace_vars(list_expr, variables)
                    # Xử lý danh sách: "a, b, c" hoặc a,b,c
                    if (list_expr.startswith('"') and list_expr.endswith('"')) or (list_expr.startswith("'") and list_expr.endswith("'")):
                        list_expr = list_expr[1:-1]
                    items = [item.strip() for item in list_expr.split(',') if item.strip() != '']
                    if not items:
                        # Bỏ qua khối FOREACH
                        nested = 1
                        j = i + 1
                        while j < len(raw_lines):
                            l = raw_lines[j].strip()
                            if l.startswith('FOREACH '):
                                nested += 1
                            elif l == 'ENDFOREACH':
                                nested -= 1
                                if nested == 0:
                                    break
                            j += 1
                        i = j + 1
                        continue
                    foreach_stack.append((i, items, 0, var_name))
                    variables[var_name] = items[0]
                    i += 1
                    continue

                if line == 'ENDFOREACH':
                    if not foreach_stack:
                        print('❌ Lỗi: ENDFOREACH không có FOREACH')
                        i += 1
                        continue
                    start_line, items, idx, var_name = foreach_stack.pop()
                    idx += 1
                    if idx < len(items):
                        foreach_stack.append((start_line, items, idx, var_name))
                        variables[var_name] = items[idx]
                        i = start_line + 1
                    else:
                        if var_name in variables:
                            del variables[var_name]
                        i += 1
                    continue

                # ----- Lệnh thường (không phải cấu trúc điều khiển) -----
                self._execute_line(line, variables, auto_input_queue, original_input)
                time.sleep(delay)
                i += 1

        finally:
            builtins.input = original_input
            recorder_is_playing = False


plugin_info = {
    'enabled': True,
    'register': lambda assistant: assistant.handlers.append(MacroCommandHandler(assistant)),
    'methods': [],
    'classes': [MacroRecorder, MacroCommandHandler],
    'description': 'Ghi và chạy macro với đầy đủ tính năng: INPUT, SET, ?, PRINT, LOOP, FOREACH, FUNCTION/CALL/RETURN, IF/ELSE/ENDIF'
}