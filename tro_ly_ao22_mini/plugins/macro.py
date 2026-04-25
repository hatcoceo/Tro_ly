# Thêm từ khóa pass, finally, assert, del, from 
import ast
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

class AssertionFailedError(Exception):
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
        
        for op in ['IS NOT', 'NOT IN']:
            if op in cond:
                left, right = cond.split(op, 1)
                left_val = ConditionEvaluator._cast_value(left.strip(), variables)
                right_val = ConditionEvaluator._cast_value(right.strip(), variables)
                if op == 'IS NOT':
                    return left_val is not right_val
                elif op == 'NOT IN':
                    return not ConditionEvaluator._check_in(left_val, right_val)
        
        for op in ['IS', 'IN']:
            if op in cond:
                left, right = cond.split(op, 1)
                left_val = ConditionEvaluator._cast_value(left.strip(), variables)
                right_val = ConditionEvaluator._cast_value(right.strip(), variables)
                if op == 'IS':
                    return left_val is right_val
                elif op == 'IN':
                    return ConditionEvaluator._check_in(left_val, right_val)
        
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
    def _check_in(left_val, right_val) -> bool:
        try:
            if isinstance(right_val, (str, list, tuple, set, dict)):
                return left_val in right_val
            else:
                return str(left_val) in str(right_val)
        except TypeError:
            return False

    @staticmethod
    def _cast_value(val: str, variables: Dict[str, Any]):
        val = VariableResolver.evaluate_arithmetic(val, variables)
        if isinstance(val, (int, float, bool)):
            return val
        val = StringUtils.strip_quotes(str(val))
        if val.lower() == 'none':
            return None
        if val.lower() == 'true':
            return True
        if val.lower() == 'false':
            return False
        
        if val.startswith(('[', '{', '(')) and val.endswith((']', '}', ')')):
            try:
                return ast.literal_eval(val)
            except (SyntaxError, ValueError):
                pass
        
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
        self.python_namespace = {}

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
    def __init__(self, macro_name: str, functions_only: Optional[List[str]] = None):
        self.macro_name = macro_name
        self.functions_only = functions_only  # None = import tất cả, list = chỉ import các hàm tên này

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
        
        # Nếu chỉ import một số hàm
        if self.functions_only is not None:
            for fname in self.functions_only:
                if fname in imported_functions:
                    if fname in ctx.functions:
                        print(f'⚠️ Hàm "{fname}" bị ghi đè bởi import {self.macro_name}')
                    ctx.functions[fname] = imported_functions[fname]
                else:
                    print(f'❌ Hàm "{fname}" không tồn tại trong macro {self.macro_name}')
        else:
            for fname, fbody in imported_functions.items():
                if fname in ctx.functions:
                    print(f'⚠️ Hàm "{fname}" bị ghi đè bởi import {self.macro_name}')
                ctx.functions[fname] = fbody
        
        sub_ctx = MacroContext(ctx.assistant, ctx.delay, ctx.auto_input.original_input)
        sub_ctx.variables = ctx.variables.copy()
        sub_ctx.functions = ctx.functions
        sub_ctx.auto_input = ctx.auto_input
        sub_ctx.python_namespace = ctx.python_namespace
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
        self.store_var = store_var

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        cmd = VariableResolver.resolve(self.command_text, ctx.variables)
        print(f'⏩ {cmd}')
        result = ctx.assistant.process_command(cmd)
        if self.store_var:
            ctx.variables[self.store_var] = result
        return None

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
        self.conditions_blocks = conditions_blocks
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
    def __init__(self, func_name: str, args: List[str], store_var: Optional[str] = None):
        self.func_name = func_name
        self.args = args
        self.store_var = store_var

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        if self.func_name not in ctx.functions:
            print(f'❌ Hàm không tồn tại: {self.func_name}')
            return None
        params, func_body = ctx.functions[self.func_name]
        if len(self.args) != len(params):
            print(f'❌ Hàm {self.func_name} cần {len(params)} tham số, nhận {len(self.args)}')
            return None 

        sub_ctx = MacroContext(ctx.assistant, ctx.delay, ctx.auto_input.original_input)
        sub_ctx.variables = ctx.variables.copy()
        sub_ctx.functions = ctx.functions
        sub_ctx.python_namespace = ctx.python_namespace

        for param, arg_expr in zip(params, self.args):
            arg_value = VariableResolver.evaluate_arithmetic(arg_expr, ctx.variables)
            sub_ctx.variables[param] = arg_value

        ret = func_body.execute(sub_ctx)

        if self.store_var is not None and ret is not None:
            ctx.variables[self.store_var] = ret
        return None

class BreakCommand(MacroCommand):
    def execute(self, ctx: MacroContext) -> Optional[Any]:
        raise BreakException()

class ContinueCommand(MacroCommand):
    def execute(self, ctx: MacroContext) -> Optional[Any]:
        raise ContinueException()

class RaiseCommand(MacroCommand):
    def __init__(self, expr: str):
        self.expr = expr

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        resolved = VariableResolver.resolve(self.expr, ctx.variables)
        namespace = ctx.python_namespace
        if '__builtins__' not in namespace:
            namespace['__builtins__'] = __builtins__
        try:
            obj = eval(resolved, namespace, {})
        except Exception as e:
            raise Exception(f"Lỗi khi đánh giá RAISE: {e}") from e

        if isinstance(obj, Exception):
            exc = obj
        elif isinstance(obj, type) and issubclass(obj, Exception):
            exc = obj()
        elif isinstance(obj, str):
            exc = Exception(obj)
        else:
            exc = Exception(repr(obj))
        raise exc

# ---------- Lệnh mới: ASSERT ----------
class AssertCommand(MacroCommand):
    def __init__(self, condition: str, message: Optional[str] = None):
        self.condition = condition
        self.message = message

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        cond = ConditionEvaluator.evaluate(self.condition, ctx.variables)
        if not cond:
            msg = self.message if self.message else f"ASSERT thất bại: {self.condition}"
            msg = VariableResolver.resolve_stripped(msg, ctx.variables)
            raise AssertionFailedError(msg)
        return None

# ---------- Lệnh mới: DEL ----------
class DelCommand(MacroCommand):
    def __init__(self, var_name: str):
        self.var_name = var_name

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        if self.var_name in ctx.variables:
            del ctx.variables[self.var_name]
        else:
            print(f"⚠️ Biến '{self.var_name}' không tồn tại để xóa")
        return None

# ---------- Lệnh mới: PASS ----------
class PassCommand(MacroCommand):
    def execute(self, ctx: MacroContext) -> Optional[Any]:
        return None

# ---------- Lệnh TRY mở rộng với FINALLY ----------
class TryCommand(MacroCommand):
    def __init__(self, try_block: BlockCommand, catches: List[Tuple[Optional[str], Optional[str], BlockCommand]], finally_block: Optional[BlockCommand] = None):
        self.try_block = try_block
        self.catches = catches
        self.finally_block = finally_block

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        exc_raised = None
        try:
            return self.try_block.execute(ctx)
        except Exception as e:
            exc_raised = e
            for exc_type, var_name, block in self.catches:
                if exc_type is None or exc_type == type(e).__name__:
                    if var_name:
                        ctx.variables[var_name] = e
                    else:
                        ctx.variables['exception'] = e
                    ret = block.execute(ctx)
                    if self.finally_block:
                        self.finally_block.execute(ctx)
                    return ret
            # Nếu không có catch phù hợp, chưa raise ngay, để finally xử lý
            if self.finally_block:
                self.finally_block.execute(ctx)
            raise
        finally:
            if self.finally_block and exc_raised is None:
                # Nếu không có exception hoặc đã được catch, vẫn chạy finally
                self.finally_block.execute(ctx)

# ---------- Lệnh mới: MATCH ----------
class MatchCommand(MacroCommand):
    def __init__(self, value_expr: str, cases: List[Tuple[str, BlockCommand]], default_block: Optional[BlockCommand] = None):
        self.value_expr = value_expr
        self.cases = cases
        self.default_block = default_block

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        value = VariableResolver.evaluate_arithmetic(self.value_expr, ctx.variables)
        for pattern, block in self.cases:
            if pattern == '_':
                return block.execute(ctx)
            pat_val = VariableResolver.evaluate_arithmetic(pattern, ctx.variables)
            if value == pat_val:
                return block.execute(ctx)
        if self.default_block:
            return self.default_block.execute(ctx)
        return None

# ---------- Lệnh mới: WITH ----------
class WithCommand(MacroCommand):
    def __init__(self, context_expr: str, as_var: Optional[str], body: BlockCommand):
        self.context_expr = context_expr
        self.as_var = as_var
        self.body = body

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        resolved = VariableResolver.resolve(self.context_expr, ctx.variables)
        namespace = ctx.python_namespace
        if '__builtins__' not in namespace:
            namespace['__builtins__'] = __builtins__
        try:
            obj = eval(resolved, namespace, {})
        except Exception as e:
            print(f"❌ Lỗi WITH: không thể tạo context từ '{resolved}' - {e}")
            return None
        try:
            enter_result = obj.__enter__()
        except AttributeError:
            print(f"❌ Lỗi WITH: object {obj} không hỗ trợ context manager")
            return None
        if self.as_var is not None:
            ctx.variables[self.as_var] = enter_result
        ret = None
        exc_info = None
        try:
            ret = self.body.execute(ctx)
        except Exception as e:
            exc_info = (type(e), e, e.__traceback__)
        try:
            if exc_info:
                obj.__exit__(*exc_info)
            else:
                obj.__exit__(None, None, None)
        except Exception as e:
            if not exc_info:
                raise
            else:
                raise e
        if exc_info:
            raise exc_info[1]
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
                       find_else: bool = False, find_elif: bool = False, find_finally: bool = False) -> Tuple[int, List[Tuple[str, int]]]:
        """
        Tìm vị trí kết thúc của block và danh sách các vị trí đặc biệt (ELIF, ELSE, FINALLY).
        Trả về (vị trí end, danh sách (type, line_number)).
        """
        nested = 1
        j = start + 1
        extra_positions = []
        while j < end:
            line = lines[j].strip()
            if line.startswith(start_prefix):
                nested += 1
            elif line == end_keyword:
                nested -= 1
                if nested == 0:
                    break
            elif nested == 1:
                if find_elif and line.startswith('ELIF '):
                    extra_positions.append(('elif', j))
                elif find_else and line == 'ELSE':
                    extra_positions.append(('else', j))
                elif find_finally and line == 'FINALLY':
                    extra_positions.append(('finally', j))
            j += 1
        return j, extra_positions

    @staticmethod
    def parse(lines: List[str]) -> Tuple[BlockCommand, Dict[str, Tuple[List[str], BlockCommand]]]:
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
                import re
                rest = line[9:].strip()
                match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$', rest)
                if match:
                    func_name = match.group(1)
                    params_str = match.group(2)
                    params = [p.strip().split('=')[0].strip() for p in params_str.split(',') if p.strip()]
                else:
                    func_name = rest
                    params = []
                j, _ = MacroParser.find_block_end(lines, i, end, 'FUNCTION ', 'ENDFUNCTION')
                body_children, _ = MacroParser._parse_sequence(lines, i+1, j, functions)
                functions[func_name] = (params, BlockCommand(body_children))
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
    conditions_blocks = []
    current_start = pos + 1
    for typ, idx in extra:
        if typ == 'elif':
            elif_line = lines[idx].strip()
            elif_cond = elif_line[5:].strip()
            block_children, _ = MacroParser._parse_sequence(lines, current_start, idx, functions)
            conditions_blocks.append((condition, BlockCommand(block_children)))
            condition = elif_cond
            current_start = idx + 1
        elif typ == 'else':
            block_children, _ = MacroParser._parse_sequence(lines, current_start, idx, functions)
            conditions_blocks.append((condition, BlockCommand(block_children)))
            else_children, _ = MacroParser._parse_sequence(lines, idx+1, j, functions)
            return IfCommand(conditions_blocks, BlockCommand(else_children)), j+1
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
        call_part = parts[0].strip()
        store_var = parts[1].strip()
    else:
        call_part = rest
    import re
    match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$', call_part)
    if match:
        func_name = match.group(1)
        args_str = match.group(2)
        args = [arg.strip() for arg in args_str.split(',') if arg.strip()]
    else:
        func_name = call_part
        args = []
    return CallCommand(func_name, args, store_var), pos+1

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
    if line.startswith('IMPORT '):
        macro_name = line[7:].strip()
        if not macro_name:
            print('❌ Cú pháp: IMPORT <tên_macro>')
            return None, pos+1
        return ImportCommand(macro_name), pos+1
    return None, pos

@CommandRegistry.register
def parse_from_import(lines, pos, end, functions):
    line = lines[pos].strip()
    if not line.startswith('FROM '):
        return None, pos
    # Cú pháp: FROM macro_name IMPORT func1, func2, ...
    rest = line[5:].strip()
    if ' IMPORT ' not in rest:
        return None, pos
    macro_part, funcs_part = rest.split(' IMPORT ', 1)
    macro_name = macro_part.strip()
    if not macro_name:
        print('❌ Cú pháp: FROM <macro> IMPORT <func1, func2>')
        return None, pos+1
    func_names = [f.strip() for f in funcs_part.split(',') if f.strip()]
    if not func_names:
        print('❌ FROM IMPORT: danh sách hàm rỗng')
        return None, pos+1
    return ImportCommand(macro_name, functions_only=func_names), pos+1

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
    return PythonCommand(rest, store_var), pos+1

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
        return None, pos+1
    code_lines = []
    for k in range(pos+1, j):
        code_lines.append(lines[k].rstrip('\n'))
    raw_code = '\n'.join(code_lines)
    code = textwrap.dedent(raw_code)
    return PythonBlockCommand(code, store_var), j+1

@CommandRegistry.register
def parse_break(lines, pos, end, functions):
    line = lines[pos].strip()
    if line == 'BREAK':
        return BreakCommand(), pos+1
    return None, pos

@CommandRegistry.register
def parse_continue(lines, pos, end, functions):
    line = lines[pos].strip()
    if line == 'CONTINUE':
        return ContinueCommand(), pos+1
    return None, pos

@CommandRegistry.register
def parse_try(lines, pos, end, functions):
    line = lines[pos].strip()
    if line != 'TRY':
        return None, pos
    j, extra = MacroParser.find_block_end(lines, pos, end, 'TRY', 'ENDTRY', find_finally=True)
    catches = []
    finally_block = None
    current = pos + 1
    # Tìm các khối EXCEPT và FINALLY
    # extra là list (type, idx) theo thứ tự xuất hiện
    # Chúng ta sẽ xử lý tuần tự
    blocks_info = []  # (type, start, end)
    # Đánh dấu các vị trí bắt đầu của từng khối
    # Đơn giản: duyệt từ pos+1 đến j, nhận biết EXCEPT và FINALLY
    i = pos + 1
    while i < j:
        curr = lines[i].strip()
        if curr.startswith('EXCEPT'):
            # Tìm vị trí kết thúc của block EXCEPT này (gặp EXCEPT tiếp theo, FINALLY, hoặc ENDTRY)
            end_block = i+1
            while end_block < j:
                nxt = lines[end_block].strip()
                if nxt.startswith('EXCEPT') or nxt == 'FINALLY' or nxt == 'ENDTRY':
                    break
                end_block += 1
            blocks_info.append(('except', i, end_block))
            i = end_block
        elif curr == 'FINALLY':
            end_block = i+1
            while end_block < j and lines[end_block].strip() != 'ENDTRY':
                end_block += 1
            blocks_info.append(('finally', i, end_block))
            i = end_block
        else:
            i += 1
    
    # Xây dựng catches và finally_block
    try_end = pos + 1
    # Nếu có block EXCEPT đầu tiên thì try block kết thúc tại vị trí bắt đầu của EXCEPT đầu tiên
    except_starts = [idx for typ, idx, _ in blocks_info if typ == 'except']
    if except_starts:
        try_end = except_starts[0]
    elif any(typ == 'finally' for typ, _, _ in blocks_info):
        # Nếu không có EXCEPT nhưng có FINALLY, try block kết thúc tại FINALLY
        finally_start = next(idx for typ, idx, _ in blocks_info if typ == 'finally')
        try_end = finally_start
    else:
        try_end = j
    try_children, _ = MacroParser._parse_sequence(lines, pos+1, try_end, functions)
    try_block = BlockCommand(try_children)
    
    for typ, start, end_block in blocks_info:
        if typ == 'except':
            # Parse dòng EXCEPT
            exc_line = lines[start].strip()
            parts = exc_line.split()
            exc_type = None
            var_name = None
            if len(parts) >= 2:
                if parts[1].lower() == 'as':
                    if len(parts) >= 3:
                        var_name = parts[2]
                else:
                    exc_type = parts[1]
                    if len(parts) >= 3 and parts[2].lower() == 'as':
                        if len(parts) >= 4:
                            var_name = parts[3]
            body_children, _ = MacroParser._parse_sequence(lines, start+1, end_block, functions)
            catches.append((exc_type, var_name, BlockCommand(body_children)))
        elif typ == 'finally':
            body_children, _ = MacroParser._parse_sequence(lines, start+1, end_block, functions)
            finally_block = BlockCommand(body_children)
    return TryCommand(try_block, catches, finally_block), j+1

@CommandRegistry.register
def parse_match(lines, pos, end, functions):
    line = lines[pos].strip()
    if not line.startswith('MATCH '):
        return None, pos
    value_expr = line[6:].strip()
    j, _ = MacroParser.find_block_end(lines, pos, end, 'MATCH ', 'ENDMATCH')
    cases = []
    default_block = None
    current = pos + 1
    while current < j:
        curr_line = lines[current].strip()
        if curr_line.startswith('CASE '):
            pattern = curr_line[5:].strip()
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
    return MatchCommand(value_expr, cases, default_block), j+1

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
    return WithCommand(context_expr, as_var, BlockCommand(body_children)), j+1

@CommandRegistry.register
def parse_raise(lines, pos, end, functions):
    line = lines[pos].strip()
    if not line.startswith('RAISE '):
        return None, pos
    expr = line[6:].strip()
    if not expr:
        print('❌ Cú pháp: RAISE <exception_expression>')
        return None, pos+1
    return RaiseCommand(expr), pos+1

# ---------- Parser cho các lệnh mới ----------
@CommandRegistry.register
def parse_assert(lines, pos, end, functions):
    line = lines[pos].strip()
    if not line.startswith('ASSERT '):
        return None, pos
    rest = line[7:].strip()
    message = None
    if ',' in rest:
        cond_part, msg_part = rest.split(',', 1)
        condition = cond_part.strip()
        message = msg_part.strip()
    else:
        condition = rest
    return AssertCommand(condition, message), pos+1

@CommandRegistry.register
def parse_del(lines, pos, end, functions):
    line = lines[pos].strip()
    if not line.startswith('DEL '):
        return None, pos
    var_name = line[4:].strip()
    if not var_name:
        print('❌ Cú pháp: DEL <tên_biến>')
        return None, pos+1
    return DelCommand(var_name), pos+1

@CommandRegistry.register
def parse_pass(lines, pos, end, functions):
    line = lines[pos].strip()
    if line == 'PASS':
        return PassCommand(), pos+1
    return None, pos

@CommandRegistry.register
def parse_regular(lines, pos, end, functions):
    line = lines[pos].strip()
    if line.startswith(('FUNCTION ', 'IF ', 'LOOP ', 'FOREACH ', 'WHILE ', 'CALL ', 'SET ', 'INPUT ', 'PRINT ', '? ', 'RETURN ', 'IMPORT ', 'FROM ', 'PYTHON ', 'PYBLOCK ', 'BREAK', 'CONTINUE', 'TRY', 'MATCH ', 'WITH ', 'RAISE ', 'ASSERT ', 'DEL ', 'PASS')):
        return None, pos
    if ' -> ' in line:
        cmd, var = line.split(' -> ', 1)
        return RegularCommand(cmd.strip(), var.strip()), pos+1
    return RegularCommand(line), pos+1

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
        except AssertionFailedError as e:
            print(f"❌ ASSERT lỗi: {e}")
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
    'description': 'Ghi và chạy macro với IF/ELIF/ELSE, LOOP, FOREACH, WHILE, FUNCTION/CALL/RETURN, INPUT, SET, ?, PRINT, IMPORT, FROM IMPORT, PYTHON, BREAK, CONTINUE, TRY/FINALLY/EXCEPT, MATCH/CASE, WITH, ASSERT, DEL, PASS, RAISE'
}