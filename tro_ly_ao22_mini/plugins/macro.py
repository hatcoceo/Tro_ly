# thêm : lấy giá trị trả lời của trợ lý ảo lưu vào biến store_var
import textwrap
import os
import sys
import time
import builtins
import random
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Callable

# ==============================
# 1. Cấu hình và biến toàn cục
# ==============================
macro_folder = 'macros'
os.makedirs(macro_folder, exist_ok=True)
recorder_is_playing = False

# ==============================
# 1b. Exception cho break/continue
# ==============================
class BreakException(Exception):
    pass

class ContinueException(Exception):
    pass

# ==============================
# 2. Macro Recorder (giữ nguyên)
# ==============================
class MacroRecorder:
    def __init__(self):
        self.recording = False
        self.commands = []
        self.current_macro_name = None

    def start(self, macro_name: str):
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

# ==============================
# 3. Các lớp tiện ích (DRY)
# ==============================
class StringUtils:
    @staticmethod
    def strip_quotes(s: str) -> str:
        s = s.strip()
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            return s[1:-1]
        return s

class VariableResolver:
    @staticmethod
    def resolve(text: str, variables: Dict[str, Any]) -> str:
        for key, val in variables.items():
            text = text.replace(f'{{{key}}}', str(val))
        return text

    @staticmethod
    def resolve_stripped(text: str, variables: Dict[str, Any]) -> str:
        resolved = VariableResolver.resolve(text, variables)
        return StringUtils.strip_quotes(resolved)

    @staticmethod
    def evaluate_arithmetic(expr: str, variables: Dict[str, Any]):
        expr = VariableResolver.resolve(expr, variables).strip()
        expr = StringUtils.strip_quotes(expr)

        try:
            allowed_names = {"abs": abs, "round": round}
            code = compile(expr, "<string>", "eval")
            for name in code.co_names:
                if name not in allowed_names:
                    raise NameError(f"Không cho phép sử dụng {name}")
            result = eval(code, {"__builtins__": {}}, allowed_names)
            return result
        except Exception:
            return expr

class ConditionEvaluator:
    @staticmethod
    def evaluate(condition: str, variables: Dict[str, Any]) -> bool:
        cond = VariableResolver.resolve(condition, variables).strip()
        cond = re.sub(r'\bTRUE\b', '##TRUE##', cond, flags=re.IGNORECASE)
        cond = re.sub(r'\bFALSE\b', '##FALSE##', cond, flags=re.IGNORECASE)
        return ConditionEvaluator._evaluate_logic(cond, variables)

    @staticmethod
    def _evaluate_logic(expr: str, variables: Dict[str, Any]) -> bool:
        expr = expr.strip()
        if not expr:
            return False
        expr = re.sub(r'\band\b', 'AND', expr, flags=re.IGNORECASE)
        expr = re.sub(r'\bor\b', 'OR', expr, flags=re.IGNORECASE)
        expr = re.sub(r'\bnot\b', 'NOT', expr, flags=re.IGNORECASE)

        or_pos = ConditionEvaluator._find_operator_outside_parens(expr, ' OR ')
        if or_pos != -1:
            left = expr[:or_pos].strip()
            right = expr[or_pos + 4:].strip()
            return (ConditionEvaluator._evaluate_logic(left, variables) or
                    ConditionEvaluator._evaluate_logic(right, variables))

        and_pos = ConditionEvaluator._find_operator_outside_parens(expr, ' AND ')
        if and_pos != -1:
            left = expr[:and_pos].strip()
            right = expr[and_pos + 5:].strip()
            return (ConditionEvaluator._evaluate_logic(left, variables) and
                    ConditionEvaluator._evaluate_logic(right, variables))

        if expr.startswith('NOT '):
            sub = expr[4:].strip()
            return not ConditionEvaluator._evaluate_logic(sub, variables)

        if expr.startswith('(') and expr.endswith(')'):
            return ConditionEvaluator._evaluate_logic(expr[1:-1], variables)

        return ConditionEvaluator._evaluate_comparison(expr, variables)

    @staticmethod
    def _find_operator_outside_parens(expr: str, op: str) -> int:
        depth = 0
        i = 0
        while i < len(expr):
            ch = expr[i]
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            elif depth == 0 and expr[i:i+len(op)] == op:
                return i
            i += 1
        return -1

    @staticmethod
    def _evaluate_comparison(cond: str, variables: Dict[str, Any]) -> bool:
        cond = cond.replace('##TRUE##', 'True').replace('##FALSE##', 'False')
        for op in ['==', '!=', '>=', '<=', '>', '<']:
            if op in cond:
                left, right = cond.split(op, 1)
                left_val = ConditionEvaluator._cast_value(left.strip(), variables)
                right_val = ConditionEvaluator._cast_value(right.strip(), variables)
                if op == '==': return left_val == right_val
                if op == '!=': return left_val != right_val
                if op == '>': return left_val > right_val
                if op == '<': return left_val < right_val
                if op == '>=': return left_val >= right_val
                if op == '<=': return left_val <= right_val
        val = ConditionEvaluator._cast_value(cond, variables)
        return bool(val)

    @staticmethod
    def _cast_value(val: str, variables: Dict[str, Any]):
        val = VariableResolver.evaluate_arithmetic(val, variables)
        if isinstance(val, (int, float, bool)):
            return val
        val = StringUtils.strip_quotes(str(val))
        # Xử lý từ khóa NONE
        if val.lower() == 'none':
            return None
        if val.lower() == 'true':
            return True
        if val.lower() == 'false':
            return False
        try:
            if '.' in val:
                return float(val)
            return int(val)
        except ValueError:
            return val

class AutoInputHelper:
    def __init__(self, original_input: Callable):
        self.queue: List[str] = []
        self.original_input = original_input

    def push(self, value: str):
        self.queue.append(value)

    def get_input(self, prompt: str = '') -> str:
        if self.queue:
            answer = self.queue.pop(0)
            print(f'{prompt}{answer}')
            return answer
        return self.original_input(prompt)

# ==============================
# 4. Command Pattern (bổ sung các lệnh mới)
# ==============================
class MacroContext:
    def __init__(self, assistant, delay: float, original_input: Callable):
        self.assistant = assistant
        self.delay = delay
        self.variables: Dict[str, Any] = {}
        self.auto_input = AutoInputHelper(original_input)
        self.functions: Dict[str, 'BlockCommand'] = {}
        self.python_namespace = {}          # ✅ namespace dùng chung cho PYTHON

class MacroCommand(ABC):
    @abstractmethod
    def execute(self, ctx: MacroContext) -> Optional[Any]:
        pass

class BlockCommand(MacroCommand):
    def __init__(self, children: List[MacroCommand]):
        self.children = children

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        for child in self.children:
            ret = child.execute(ctx)
            if ret is not None:
                return ret
            time.sleep(ctx.delay)
        return None

# ---------- Các lệnh đơn dòng ----------
class SetCommand(MacroCommand):
    def __init__(self, var_name: str, value_expr: str):
        self.var_name = var_name
        self.value_expr = value_expr

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        value = VariableResolver.evaluate_arithmetic(self.value_expr, ctx.variables)
        ctx.variables[self.var_name] = value
        return None

class InputCommand(MacroCommand):
    def __init__(self, value: str):
        self.value = value

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        resolved = VariableResolver.resolve_stripped(self.value, ctx.variables)
        ctx.auto_input.push(resolved)
        return None

class PrintCommand(MacroCommand):
    def __init__(self, message: str):
        self.message = message

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        msg = VariableResolver.resolve_stripped(self.message, ctx.variables)
        print(f'📢 {msg}')
        return None

class QuestionCommand(MacroCommand):
    def __init__(self, question: str, auto_answer: Optional[str] = None):
        self.question = question
        self.auto_answer = auto_answer

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        q = VariableResolver.resolve(self.question, ctx.variables)
        if self.auto_answer is not None:
            ans = VariableResolver.resolve_stripped(self.auto_answer, ctx.variables)
            print(f'🤖 (tự động) {q}\n👉 {ans}')
            user_input = ans
        else:
            user_input = ctx.auto_input.get_input(f'\n🤖 {q}\n👉 ')
        ctx.variables['answer'] = user_input
        print()
        return None

class ReturnCommand(MacroCommand):
    def __init__(self, value_expr: str):
        self.value_expr = value_expr

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        ret = VariableResolver.evaluate_arithmetic(self.value_expr, ctx.variables)
        return ret

class ImportCommand(MacroCommand):
    def __init__(self, macro_name: str):
        self.macro_name = macro_name

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        path = os.path.join(macro_folder, f'{self.macro_name}.txt')
        if not os.path.exists(path):
            print(f'❌ Không tìm thấy macro để import: {self.macro_name}')
            return None
        if hasattr(ctx, 'import_stack') and self.macro_name in ctx.import_stack:
            print(f'❌ Import vòng: {" -> ".join(ctx.import_stack + [self.macro_name])}')
            return None
        with open(path, 'r', encoding='utf-8') as f:
            raw_lines = f.readlines()
        imported_root, imported_functions = MacroParser.parse(raw_lines)
        for fname, fbody in imported_functions.items():
            if fname in ctx.functions:
                print(f'⚠️ Hàm "{fname}" bị ghi đè bởi import {self.macro_name}')
            ctx.functions[fname] = fbody
        sub_ctx = MacroContext(ctx.assistant, ctx.delay, ctx.auto_input.original_input)
        sub_ctx.variables = ctx.variables.copy()
        sub_ctx.functions = ctx.functions
        sub_ctx.auto_input = ctx.auto_input
        sub_ctx.python_namespace = ctx.python_namespace   # kế thừa namespace
        if hasattr(ctx, 'import_stack'):
            sub_ctx.import_stack = ctx.import_stack + [self.macro_name]
        else:
            sub_ctx.import_stack = [self.macro_name]
        ret = imported_root.execute(sub_ctx)
        ctx.variables.update(sub_ctx.variables)
        return ret

class RegularCommand(MacroCommand):
    def __init__(self, command_text: str, store_var: Optional[str] = None):
        self.command_text = command_text
        self.store_var = store_var   # biến mới thêm vào để lưu kết quả trả lời của trợ lý ảo

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        cmd = VariableResolver.resolve(self.command_text, ctx.variables)
        print(f'⏩ {cmd}')

        result = ctx.assistant.process_command(cmd)   # 👈 lấy kết quả

        if self.store_var:
            ctx.variables[self.store_var] = result    # 👈 lưu vào biến macro

        return None

# ---------- Lệnh PYTHON ----------
class PythonCommand(MacroCommand):
    def __init__(self, code: str, store_var: Optional[str] = None):
        self.code = code
        self.store_var = store_var

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        resolved = VariableResolver.resolve(self.code, ctx.variables)
        namespace = ctx.python_namespace
        if '__builtins__' not in namespace:
            namespace['__builtins__'] = __builtins__
        try:
            result = eval(resolved, namespace, {})
        except Exception:
            try:
                exec(resolved, namespace)
                result = None
            except Exception as e:
                print(f"❌ Lỗi PYTHON: {e}")
                return None
        if self.store_var is not None:
            ctx.variables[self.store_var] = result
        elif result is not None:
            print(f"🐍 {result}")
        return None

class PythonBlockCommand(MacroCommand):
    def __init__(self, code: str, store_var: Optional[str] = None):
        self.code = code
        self.store_var = store_var

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        namespace = ctx.python_namespace
        if '__builtins__' not in namespace:
            namespace['__builtins__'] = __builtins__

        dedented_code = textwrap.dedent(self.code)

        try:
            exec(dedented_code, namespace)
        except Exception as e:
            print(f"❌ Lỗi PYTHON BLOCK: {e}")
            return None

        if self.store_var is not None:
            if self.store_var in namespace:
                ctx.variables[self.store_var] = namespace[self.store_var]
            else:
                print(f"⚠️ Biến '{self.store_var}' không tồn tại sau khi chạy PYBLOCK")
        return None

# ---------- Lệnh cấu trúc (có bổ sung) ----------
class IfCommand(MacroCommand):
    def __init__(self, conditions_blocks: List[Tuple[str, BlockCommand]], else_block: Optional[BlockCommand] = None):
        self.conditions_blocks = conditions_blocks   # list of (condition, block)
        self.else_block = else_block

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        for condition, block in self.conditions_blocks:
            if ConditionEvaluator.evaluate(condition, ctx.variables):
                return block.execute(ctx)
        if self.else_block:
            return self.else_block.execute(ctx)
        return None

class LoopCommand(MacroCommand):
    def __init__(self, count_expr: str, body: BlockCommand):
        self.count_expr = count_expr
        self.body = body

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        count_str = VariableResolver.evaluate_arithmetic(self.count_expr, ctx.variables)
        try:
            count = int(float(count_str))
        except ValueError:
            print(f'❌ Lỗi: Số lần lặp không hợp lệ: {count_str}')
            return None
        i = 0
        while i < count:
            ctx.variables['loop_index'] = i + 1
            try:
                ret = self.body.execute(ctx)
                if ret is not None:
                    return ret
                i += 1
            except BreakException:
                break
            except ContinueException:
                i += 1
                continue
        if 'loop_index' in ctx.variables:
            del ctx.variables['loop_index']
        return None

class ForeachCommand(MacroCommand):
    def __init__(self, var_name: str, list_expr: str, body: BlockCommand):
        self.var_name = var_name
        self.list_expr = list_expr
        self.body = body

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        list_str = VariableResolver.resolve_stripped(self.list_expr, ctx.variables)
        items = [item.strip() for item in list_str.split(',') if item.strip() != '']
        for item in items:
            ctx.variables[self.var_name] = item
            try:
                ret = self.body.execute(ctx)
                if ret is not None:
                    return ret
            except BreakException:
                break
            except ContinueException:
                continue
        if self.var_name in ctx.variables:
            del ctx.variables[self.var_name]
        return None

class WhileCommand(MacroCommand):
    def __init__(self, condition: str, body: BlockCommand):
        self.condition = condition
        self.body = body

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        while ConditionEvaluator.evaluate(self.condition, ctx.variables):
            try:
                ret = self.body.execute(ctx)
                if ret is not None:
                    return ret
            except BreakException:
                break
            except ContinueException:
                continue
        return None

class CallCommand(MacroCommand):
    def __init__(self, func_name: str, store_var: Optional[str] = None):
        self.func_name = func_name
        self.store_var = store_var

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        if self.func_name not in ctx.functions:
            print(f'❌ Hàm không tồn tại: {self.func_name}')
            return None
        func_body = ctx.functions[self.func_name]
        sub_ctx = MacroContext(ctx.assistant, ctx.delay, ctx.auto_input.original_input)
        sub_ctx.variables = ctx.variables.copy()
        sub_ctx.functions = ctx.functions
        sub_ctx.python_namespace = ctx.python_namespace
        ret = func_body.execute(sub_ctx)
        if self.store_var is not None and ret is not None:
            ctx.variables[self.store_var] = ret
        return None

# ---------- Lệnh mới: BREAK, CONTINUE ----------
class BreakCommand(MacroCommand):
    def execute(self, ctx: MacroContext) -> Optional[Any]:
        raise BreakException()

class ContinueCommand(MacroCommand):
    def execute(self, ctx: MacroContext) -> Optional[Any]:
        raise ContinueException()

# ---------- Lệnh mới: TRY / CATCH ----------
class TryCommand(MacroCommand):
    def __init__(self, try_block: BlockCommand, catches: List[Tuple[Optional[str], BlockCommand]]):
        self.try_block = try_block
        self.catches = catches   # list of (exception_type_or_None, block)

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        try:
            return self.try_block.execute(ctx)
        except Exception as e:
            for exc_type, block in self.catches:
                if exc_type is None or exc_type == type(e).__name__:
                    # Lưu exception vào biến đặc biệt nếu cần
                    ctx.variables['exception'] = e
                    return block.execute(ctx)
            # Nếu không có catch phù hợp, raise lại
            raise

# ---------- Lệnh mới: MATCH (pattern matching đơn giản) ----------
class MatchCommand(MacroCommand):
    def __init__(self, value_expr: str, cases: List[Tuple[str, BlockCommand]], default_block: Optional[BlockCommand] = None):
        self.value_expr = value_expr
        self.cases = cases          # list of (pattern, block)
        self.default_block = default_block

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        value = VariableResolver.evaluate_arithmetic(self.value_expr, ctx.variables)
        for pattern, block in self.cases:
            # pattern có thể là giá trị cụ thể hoặc từ khóa _ (match all)
            if pattern == '_':
                return block.execute(ctx)
            pat_val = VariableResolver.evaluate_arithmetic(pattern, ctx.variables)
            if value == pat_val:
                return block.execute(ctx)
        if self.default_block:
            return self.default_block.execute(ctx)
        return None

# ---------- Lệnh mới: WITH (context manager) ----------
class WithCommand(MacroCommand):
    def __init__(self, context_expr: str, as_var: Optional[str], body: BlockCommand):
        self.context_expr = context_expr
        self.as_var = as_var
        self.body = body

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        # Đánh giá biểu thức context (phải trả về đối tượng có __enter__ và __exit__)
        resolved = VariableResolver.resolve(self.context_expr, ctx.variables)
        # Cho phép sử dụng các context manager Python thông qua PYTHON hoặc built-in
        # Ở đây ta eval trong python_namespace để lấy object
        namespace = ctx.python_namespace
        if '__builtins__' not in namespace:
            namespace['__builtins__'] = __builtins__
        try:
            obj = eval(resolved, namespace, {})
        except Exception as e:
            print(f"❌ Lỗi WITH: không thể tạo context từ '{resolved}' - {e}")
            return None
        # Gọi __enter__
        try:
            enter_result = obj.__enter__()
        except AttributeError:
            print(f"❌ Lỗi WITH: object {obj} không hỗ trợ context manager")
            return None
        if self.as_var is not None:
            ctx.variables[self.as_var] = enter_result
        # Thực thi khối lệnh
        ret = None
        exc_info = None
        try:
            ret = self.body.execute(ctx)
        except Exception as e:
            exc_info = (type(e), e, e.__traceback__)
            # Không raise ngay, để __exit__ xử lý
        # Gọi __exit__
        try:
            if exc_info:
                obj.__exit__(*exc_info)
            else:
                obj.__exit__(None, None, None)
        except Exception as e:
            if not exc_info:
                raise
            else:
                # Nếu __exit__ raise exception mới, ưu tiên exception mới
                raise e
        if exc_info:
            raise exc_info[1]  # raise lại exception cũ nếu __exit__ không xử lý
        return ret

# ==============================
# 5. Command Registry (OCP)
# ==============================
class CommandRegistry:
    _parsers: List[Callable] = []

    @classmethod
    def register(cls, parser_func: Callable):
        cls._parsers.append(parser_func)
        return parser_func

    @classmethod
    def parse(cls, lines: List[str], pos: int, end: int, functions: Dict) -> Tuple[Optional[MacroCommand], int]:
        line = lines[pos].strip()
        if not line:
            return None, pos + 1
        for parser in cls._parsers:
            cmd, next_pos = parser(lines, pos, end, functions)
            if cmd is not None:
                return cmd, next_pos
        return None, pos + 1

# ==============================
# 6. Macro Parser (có DRY)
# ==============================
class MacroParser:
    @staticmethod
    def find_block_end(lines: List[str], start: int, end: int,
                       start_prefix: str, end_keyword: str,
                       find_else: bool = False, find_elif: bool = False) -> Tuple[int, List[int]]:
        """
        Tìm vị trí kết thúc của block và danh sách các vị trí ELIF/ELSE.
        Trả về (vị trí end, danh sách các vị trí của ELIF và ELSE theo thứ tự).
        """
        nested = 1
        j = start + 1
        extra_positions = []   # (line_number, type) với type là 'elif' hoặc 'else'
        while j < end:
            line = lines[j].strip()
            if line.startswith(start_prefix):
                nested += 1
            elif line == end_keyword:
                nested -= 1
                if nested == 0:
                    break
            elif find_elif and line.startswith('ELIF ') and nested == 1:
                extra_positions.append(('elif', j))
            elif find_else and line == 'ELSE' and nested == 1:
                extra_positions.append(('else', j))
            j += 1
        return j, extra_positions

    @staticmethod
    def parse(lines: List[str]) -> Tuple[BlockCommand, Dict[str, BlockCommand]]:
        raw = [line.rstrip('\n') for line in lines]
        functions = {}
        root_children, _ = MacroParser._parse_sequence(raw, 0, len(raw), functions)
        return BlockCommand(root_children), functions

    @staticmethod
    def _parse_sequence(lines: List[str], start: int, end: int, functions: Dict) -> Tuple[List[MacroCommand], int]:
        children = []
        i = start
        while i < end:
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            if line.startswith('FUNCTION '):
                func_name = line[9:].strip()
                j, _ = MacroParser.find_block_end(lines, i, end, 'FUNCTION ', 'ENDFUNCTION')
                body_children, _ = MacroParser._parse_sequence(lines, i+1, j, functions)
                functions[func_name] = BlockCommand(body_children)
                i = j + 1
                continue
            if line == 'ENDFUNCTION':
                i += 1
                continue
            cmd, next_i = CommandRegistry.parse(lines, i, end, functions)
            if cmd is not None:
                children.append(cmd)
            i = next_i
        return children, i

# ==============================
# 7. Đăng ký các parser (có bổ sung)
# ==============================
@CommandRegistry.register
def parse_if(lines, pos, end, functions):
    line = lines[pos].strip()
    if not line.startswith('IF '):
        return None, pos
    condition = line[3:].strip()
    j, extra = MacroParser.find_block_end(lines, pos, end, 'IF ', 'ENDIF', find_else=True, find_elif=True)
    # Xây dựng danh sách các khối condition và else
    conditions_blocks = []
    current_start = pos + 1
    # Duyệt theo thứ tự các elif/else
    for typ, idx in extra:
        if typ == 'elif':
            # Đọc điều kiện của ELIF
            elif_line = lines[idx].strip()
            elif_cond = elif_line[5:].strip()  # bỏ "ELIF "
            # Lấy block từ current_start đến idx
            block_children, _ = MacroParser._parse_sequence(lines, current_start, idx, functions)
            conditions_blocks.append((condition, BlockCommand(block_children)))
            condition = elif_cond
            current_start = idx + 1
        elif typ == 'else':
            # Khối if cuối cùng trước else
            block_children, _ = MacroParser._parse_sequence(lines, current_start, idx, functions)
            conditions_blocks.append((condition, BlockCommand(block_children)))
            # Khối else từ idx+1 đến j
            else_children, _ = MacroParser._parse_sequence(lines, idx+1, j, functions)
            return IfCommand(conditions_blocks, BlockCommand(else_children)), j+1
    # Không có else, chỉ có các if/elif
    block_children, _ = MacroParser._parse_sequence(lines, current_start, j, functions)
    conditions_blocks.append((condition, BlockCommand(block_children)))
    return IfCommand(conditions_blocks), j+1

@CommandRegistry.register
def parse_loop(lines, pos, end, functions):
    line = lines[pos].strip()
    if not line.startswith('LOOP '):
        return None, pos
    count_expr = line[5:].strip()
    j, _ = MacroParser.find_block_end(lines, pos, end, 'LOOP ', 'ENDLOOP')
    body_children, _ = MacroParser._parse_sequence(lines, pos+1, j, functions)
    return LoopCommand(count_expr, BlockCommand(body_children)), j+1

@CommandRegistry.register
def parse_foreach(lines, pos, end, functions):
    line = lines[pos].strip()
    if not line.startswith('FOREACH '):
        return None, pos
    rest = line[8:].strip()
    if ' IN ' not in rest:
        print(f'❌ Lỗi cú pháp FOREACH: {line}')
        return None, pos+1
    var_part, list_part = rest.split(' IN ', 1)
    var_name = var_part.strip()
    list_expr = list_part.strip()
    j, _ = MacroParser.find_block_end(lines, pos, end, 'FOREACH ', 'ENDFOREACH')
    body_children, _ = MacroParser._parse_sequence(lines, pos+1, j, functions)
    return ForeachCommand(var_name, list_expr, BlockCommand(body_children)), j+1

@CommandRegistry.register
def parse_while(lines, pos, end, functions):
    line = lines[pos].strip()
    if not line.startswith('WHILE '):
        return None, pos
    condition = line[6:].strip()
    j, _ = MacroParser.find_block_end(lines, pos, end, 'WHILE ', 'ENDWHILE')
    body_children, _ = MacroParser._parse_sequence(lines, pos+1, j, functions)
    return WhileCommand(condition, BlockCommand(body_children)), j+1

@CommandRegistry.register
def parse_call(lines, pos, end, functions):
    line = lines[pos].strip()
    if not line.startswith('CALL '):
        return None, pos
    rest = line[5:].strip()
    store_var = None
    if ' -> ' in rest:
        parts = rest.split(' -> ', 1)
        func_part = parts[0].strip()
        store_var = parts[1].strip()
    else:
        func_part = rest
    return CallCommand(func_part, store_var), pos+1

@CommandRegistry.register
def parse_set(lines, pos, end, functions):
    line = lines[pos].strip()
    if not line.startswith('SET '):
        return None, pos
    parts = line[4:].split('=', 1)
    if len(parts) == 2:
        return SetCommand(parts[0].strip(), parts[1].strip()), pos+1
    return None, pos+1

@CommandRegistry.register
def parse_input(lines, pos, end, functions):
    line = lines[pos].strip()
    if not line.startswith('INPUT '):
        return None, pos
    return InputCommand(line[6:].strip()), pos+1

@CommandRegistry.register
def parse_print(lines, pos, end, functions):
    line = lines[pos].strip()
    if not line.startswith('PRINT '):
        return None, pos
    return PrintCommand(line[6:].strip()), pos+1

@CommandRegistry.register
def parse_question(lines, pos, end, functions):
    line = lines[pos].strip()
    if not line.startswith('? '):
        return None, pos
    rest = line[2:].strip()
    auto = None
    if ' auto:' in rest:
        q, a = rest.split(' auto:', 1)
        auto = a.strip()
        rest = q.strip()
    return QuestionCommand(rest, auto), pos+1

@CommandRegistry.register
def parse_return(lines, pos, end, functions):
    line = lines[pos].strip()
    if not line.startswith('RETURN '):
        return None, pos
    return ReturnCommand(line[7:].strip()), pos+1

@CommandRegistry.register
def parse_import(lines, pos, end, functions):
    line = lines[pos].strip()
    if not line.startswith('IMPORT '):
        return None, pos
    macro_name = line[7:].strip()
    if not macro_name:
        print('❌ Cú pháp: IMPORT <tên_macro>')
        return None, pos + 1
    return ImportCommand(macro_name), pos + 1

@CommandRegistry.register
def parse_python(lines, pos, end, functions):
    line = lines[pos].strip()
    if not line.startswith('PYTHON '):
        return None, pos
    rest = line[7:].strip()
    store_var = None
    if ' -> ' in rest:
        expr, var = rest.split(' -> ', 1)
        store_var = var.strip()
        rest = expr.strip()
    return PythonCommand(rest, store_var), pos + 1

@CommandRegistry.register
def parse_pyblock(lines, pos, end, functions):
    line = lines[pos].strip()
    if not line.startswith('PYBLOCK '):
        return None, pos

    rest = line[8:].strip()
    store_var = None
    if '->' in rest:
        parts = rest.split('->', 1)
        store_var = parts[1].strip()

    nested = 1
    j = pos + 1
    while j < end:
        curr = lines[j].strip()
        if curr.startswith('PYBLOCK '):
            nested += 1
        elif curr == 'ENDPYBLOCK':
            nested -= 1
            if nested == 0:
                break
        j += 1
    else:
        print("❌ Thiếu ENDPYBLOCK")
        return None, pos + 1

    code_lines = []
    for k in range(pos + 1, j):
        code_lines.append(lines[k].rstrip('\n'))
    raw_code = '\n'.join(code_lines)

    code = textwrap.dedent(raw_code)
    return PythonBlockCommand(code, store_var), j + 1

# ---------- Parser cho BREAK và CONTINUE ----------
@CommandRegistry.register
def parse_break(lines, pos, end, functions):
    line = lines[pos].strip()
    if line == 'BREAK':
        return BreakCommand(), pos + 1
    return None, pos

@CommandRegistry.register
def parse_continue(lines, pos, end, functions):
    line = lines[pos].strip()
    if line == 'CONTINUE':
        return ContinueCommand(), pos + 1
    return None, pos

# ---------- Parser cho TRY / CATCH ----------
@CommandRegistry.register
def parse_try(lines, pos, end, functions):
    line = lines[pos].strip()
    if line != 'TRY':
        return None, pos

    # Tìm khối try
    j_try, _ = MacroParser.find_block_end(lines, pos, end, 'TRY', 'ENDTRY')
    # Trong ENDTRY sẽ chứa các CATCH
    # Cần phân tích các CATCH bên trong
    catches = []
    current = pos + 1
    while current < j_try:
        curr_line = lines[current].strip()
        if curr_line.startswith('CATCH'):
            # Có thể có dạng CATCH <exception_type> hoặc CATCH (bắt mọi exception)
            parts = curr_line.split()
            exc_type = None
            if len(parts) > 1:
                exc_type = parts[1].strip()
            # Tìm block của CATCH này (kết thúc bởi CATCH khác hoặc ENDTRY)
            next_catch = current + 1
            while next_catch < j_try:
                if lines[next_catch].strip().startswith('CATCH') or lines[next_catch].strip() == 'ENDTRY':
                    break
                next_catch += 1
            body_children, _ = MacroParser._parse_sequence(lines, current+1, next_catch, functions)
            catches.append((exc_type, BlockCommand(body_children)))
            current = next_catch
        else:
            current += 1

    # Lấy try block (từ pos+1 đến trước CATCH đầu tiên hoặc đến j_try)
    try_end = pos + 1
    while try_end < j_try and not lines[try_end].strip().startswith('CATCH'):
        try_end += 1
    try_children, _ = MacroParser._parse_sequence(lines, pos+1, try_end, functions)
    try_block = BlockCommand(try_children)

    return TryCommand(try_block, catches), j_try + 1

# ---------- Parser cho MATCH ----------
@CommandRegistry.register
def parse_match(lines, pos, end, functions):
    line = lines[pos].strip()
    if not line.startswith('MATCH '):
        return None, pos
    value_expr = line[6:].strip()
    j, _ = MacroParser.find_block_end(lines, pos, end, 'MATCH ', 'ENDMATCH')
    # Phân tích các CASE bên trong
    cases = []
    default_block = None
    current = pos + 1
    while current < j:
        curr_line = lines[current].strip()
        if curr_line.startswith('CASE '):
            pattern = curr_line[5:].strip()
            # Tìm block của CASE này
            next_case = current + 1
            while next_case < j:
                nxt = lines[next_case].strip()
                if nxt.startswith('CASE ') or nxt.startswith('DEFAULT') or nxt == 'ENDMATCH':
                    break
                next_case += 1
            body_children, _ = MacroParser._parse_sequence(lines, current+1, next_case, functions)
            cases.append((pattern, BlockCommand(body_children)))
            current = next_case
        elif curr_line.startswith('DEFAULT'):
            next_default = current + 1
            while next_default < j:
                if lines[next_default].strip().startswith('CASE ') or lines[next_default].strip() == 'ENDMATCH':
                    break
                next_default += 1
            body_children, _ = MacroParser._parse_sequence(lines, current+1, next_default, functions)
            default_block = BlockCommand(body_children)
            current = next_default
        else:
            current += 1
    return MatchCommand(value_expr, cases, default_block), j + 1

# ---------- Parser cho WITH ----------
@CommandRegistry.register
def parse_with(lines, pos, end, functions):
    line = lines[pos].strip()
    if not line.startswith('WITH '):
        return None, pos
    rest = line[5:].strip()
    as_var = None
    if ' AS ' in rest:
        context_part, var_part = rest.split(' AS ', 1)
        context_expr = context_part.strip()
        as_var = var_part.strip()
    else:
        context_expr = rest
        as_var = None
    j, _ = MacroParser.find_block_end(lines, pos, end, 'WITH ', 'ENDWITH')
    body_children, _ = MacroParser._parse_sequence(lines, pos+1, j, functions)
    return WithCommand(context_expr, as_var, BlockCommand(body_children)), j + 1

# ✅ Parser cho lệnh thường (phải đăng ký SAU CÙNG)
@CommandRegistry.register
def parse_regular(lines, pos, end, functions):
    line = lines[pos].strip()

    if line.startswith(('FUNCTION ', 'IF ', 'LOOP ', 'FOREACH ', 'WHILE ', 'CALL ', 'SET ', 'INPUT ', 'PRINT ', '? ', 'RETURN ', 'IMPORT ', 'PYTHON ', 'PYBLOCK ', 'BREAK', 'CONTINUE', 'TRY', 'MATCH ', 'WITH ')):
        return None, pos

    # 👇 hỗ trợ lưu kết quả vào biến store_var
    if ' -> ' in line:
        cmd, var = line.split(' -> ', 1)
        return RegularCommand(cmd.strip(), var.strip()), pos + 1

    return RegularCommand(line), pos + 1

# ==============================
# 8. Macro Executor
# ==============================
class MacroExecutor:
    def __init__(self, ctx: MacroContext):
        self.ctx = ctx

    def execute(self, root: BlockCommand) -> None:
        global recorder_is_playing
        recorder_is_playing = True
        try:
            original_input = builtins.input
            builtins.input = self.ctx.auto_input.get_input
            root.execute(self.ctx)
        finally:
            builtins.input = original_input
            recorder_is_playing = False

# ==============================
# 9. MacroCommandHandler
# ==============================
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
                parts = rest.split()
                try:
                    delay = float(parts[-1])
                    macro_name = rest[:rest.rfind(parts[-1])].strip()
                except ValueError:
                    delay = 1.0
            self._play_macro(macro_name, delay)
            return True
        return False

    def _play_macro(self, macro_name: str, delay: float):
        path = os.path.join(macro_folder, f'{macro_name}.txt')
        if not os.path.exists(path):
            print(f'❌ Không tìm thấy macro: {macro_name}')
            return
        print(f'🏃 Đang chạy macro: {macro_name} (delay: {delay:.1f}s)')
        with open(path, 'r', encoding='utf-8') as f:
            raw_lines = f.readlines()
        root_command, functions = MacroParser.parse(raw_lines)
        ctx = MacroContext(self.assistant, delay, builtins.input)
        ctx.functions = functions
        executor = MacroExecutor(ctx)
        executor.execute(root_command)

# ==============================
# 10. Plugin info
# ==============================
plugin_info = {
    'enabled': True,
    'register': lambda assistant: assistant.handlers.append(MacroCommandHandler(assistant)),
    'methods': [],
    'classes': [MacroRecorder, MacroCommandHandler],
    'description': 'Ghi và chạy macro với IF/ELIF/ELSE, LOOP, FOREACH, WHILE, FUNCTION/CALL/RETURN, INPUT, SET, ?, PRINT, IMPORT, PYTHON, BREAK, CONTINUE, TRY/CATCH, MATCH/CASE, WITH'
}