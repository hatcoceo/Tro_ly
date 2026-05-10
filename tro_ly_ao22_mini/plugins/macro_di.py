# macro.py - OCP Complete Refactor
import ast
import textwrap
import os
import sys
import time
import builtins
import random
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Callable, Type

# ==============================
# 0. Registry hoàn chỉnh (có factory)
# ==============================
class MacroRegistry:
    """Trung tâm đăng ký các thành phần có thể thay thế"""
    def __init__(self):
        # Command classes
        self.set_command_class: Type = None
        self.input_command_class: Type = None
        self.print_command_class: Type = None
        self.question_command_class: Type = None
        self.return_command_class: Type = None
        self.import_command_class: Type = None
        self.regular_command_class: Type = None
        self.python_command_class: Type = None
        self.python_block_command_class: Type = None
        self.if_command_class: Type = None
        self.loop_command_class: Type = None
        self.foreach_command_class: Type = None
        self.while_command_class: Type = None
        self.call_command_class: Type = None
        self.break_command_class: Type = None
        self.continue_command_class: Type = None
        self.raise_command_class: Type = None
        self.assert_command_class: Type = None
        self.del_command_class: Type = None
        self.pass_command_class: Type = None
        self.quiet_command_class: Type = None
        self.try_command_class: Type = None
        self.match_command_class: Type = None
        self.with_command_class: Type = None

        # Helper classes
        self.string_utils_class: Type = None
        self.variable_resolver_class: Type = None
        self.condition_evaluator_class: Type = None
        self.auto_input_helper_class: Type = None

        # Parser class
        self.macro_parser_class: Type = None

        # Executor and context
        self.macro_context_class: Type = None
        self.macro_executor_class: Type = None
        self.macro_command_handler_class: Type = None

        # Command registry (list of parser functions)
        self.command_parsers: List[Callable] = []

    def register_parser(self, parser_func: Callable):
        self.command_parsers.append(parser_func)

    def get_command_class(self, name: str) -> Type:
        return getattr(self, f"{name}_command_class", None)

    # ----- Factory methods cho phép ghi đè -----
    def create_context(self, assistant, delay: float, original_input: Callable) -> 'MacroContext':
        """Tạo MacroContext mới, có thể ghi đè bằng class con."""
        return self.macro_context_class(assistant, delay, original_input, registry=self)

    def create_auto_input(self, original_input: Callable) -> 'AutoInputHelper':
        return self.auto_input_helper_class(original_input)

    def create_parser(self) -> 'MacroParser':
        return self.macro_parser_class()

    def create_executor(self, ctx: 'MacroContext') -> 'MacroExecutor':
        return self.macro_executor_class(ctx)

    def create_command_handler(self, assistant) -> 'MacroCommandHandler':
        return self.macro_command_handler_class(assistant)

# Registry toàn cục
_global_registry = MacroRegistry()

def get_registry() -> MacroRegistry:
    return _global_registry

# ==============================
# 1. Cấu hình và biến toàn cục
# ==============================
macro_folder = 'macros'
os.makedirs(macro_folder, exist_ok=True)
recorder_is_playing = False

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
# 3. Các lớp tiện ích
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
    def substitute(text: str, variables: Dict[str, Any], ctx: Optional['MacroContext'] = None) -> str:
        def repl_braced(match):
            expr = match.group(1)
            try:
                val = VariableResolver.evaluate_arithmetic(expr, variables, ctx=ctx)
                return str(val)
            except Exception:
                return f'${{{expr}}}'
        def repl_dollar(match):
            name = match.group(1)
            if name in variables:
                return str(variables[name])
            return f'${name}'
        text = re.sub(r'\$\{([^{}]+)\}', repl_braced, text)
        text = re.sub(r'(?<!\$)\$([a-zA-Z_][a-zA-Z0-9_]*)', repl_dollar, text)
        return text

    @staticmethod
    def resolve(text: str, variables: Dict[str, Any]) -> str:
        def repl(match):
            name = match.group(1)
            return str(variables.get(name, f'${name}'))
        return re.sub(r'\$([a-zA-Z_][a-zA-Z0-9_]*)', repl, text)

    @staticmethod
    def resolve_stripped(text: str, variables: Dict[str, Any]) -> str:
        resolved = VariableResolver.resolve(text, variables)
        return StringUtils.strip_quotes(resolved)

    @staticmethod
    def evaluate_arithmetic(expr: str, variables: Dict[str, Any], ctx: Optional['MacroContext'] = None) -> Any:
        expr = VariableResolver.substitute(expr, variables, ctx=ctx).strip()
        if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
            return expr[1:-1]
        namespace = {**variables}
        if ctx:
            def make_wrapper(func_name, func_info):
                if len(func_info) == 3:
                    params, defaults, body = func_info
                else:
                    params, body = func_info
                    defaults = {}
                def wrapper(*args, **kwargs):
                    # Dùng factory từ registry của ctx
                    sub_ctx = ctx.registry.create_context(ctx.assistant, ctx.delay, ctx.auto_input.original_input)
                    sub_ctx.variables = ctx.variables.copy()
                    sub_ctx.functions = ctx.functions
                    sub_ctx.python_namespace = ctx.python_namespace
                    sub_ctx.auto_input = ctx.auto_input
                    sub_ctx.quiet = ctx.quiet
                    arg_map = {}
                    for i, arg in enumerate(args):
                        if i >= len(params):
                            raise TypeError(f"{func_name} takes at most {len(params)} positional arguments")
                        arg_map[params[i]] = arg
                    for k, v in kwargs.items():
                        if k not in params:
                            raise TypeError(f"{func_name} got unexpected keyword argument '{k}'")
                        if k in arg_map:
                            raise TypeError(f"{func_name} got multiple values for argument '{k}'")
                        arg_map[k] = v
                    for param in params:
                        if param not in arg_map:
                            if param in defaults:
                                default_val = VariableResolver.evaluate_arithmetic(defaults[param], sub_ctx.variables, ctx=sub_ctx)
                                arg_map[param] = default_val
                            else:
                                raise TypeError(f"{func_name} missing required argument '{param}'")
                    for param, val in arg_map.items():
                        sub_ctx.variables[param] = val
                    ret = body.execute(sub_ctx)
                    return ret
                return wrapper
            for fname, finfo in ctx.functions.items():
                namespace[fname] = make_wrapper(fname, finfo)
        namespace.update({
            'abs': abs, 'round': round, 'len': len,
            'str': str, 'int': int, 'float': float,
            'list': list, 'dict': dict, 'set': set, 'tuple': tuple, 'zip': zip, 'range': range, 'map': map,
            'min': min, 'max': max, 'sum': sum, 
            'all': all, 'any': any, 'filter': filter, 'enumerate': enumerate,
            'True': True, 'False': False, 'None': None
        })
        try:
            result = eval(expr, {"__builtins__": {}}, namespace)
            return result
        except Exception:
            return expr

class ConditionEvaluator:
    @staticmethod
    def evaluate(condition: str, variables: Dict[str, Any], ctx: Optional['MacroContext'] = None) -> bool:
        cond = VariableResolver.substitute(condition, variables, ctx=ctx).strip()
        cond = re.sub(r'\bTRUE\b', '##TRUE##', cond, flags=re.IGNORECASE)
        cond = re.sub(r'\bFALSE\b', '##FALSE##', cond, flags=re.IGNORECASE)
        return ConditionEvaluator._evaluate_logic(cond, variables, ctx)

    @staticmethod
    def _evaluate_logic(expr: str, variables: Dict[str, Any], ctx: Optional['MacroContext'] = None) -> bool:
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
            return (ConditionEvaluator._evaluate_logic(left, variables, ctx) or
                    ConditionEvaluator._evaluate_logic(right, variables, ctx))
        and_pos = ConditionEvaluator._find_operator_outside_parens(expr, ' AND ')
        if and_pos != -1:
            left = expr[:and_pos].strip()
            right = expr[and_pos + 5:].strip()
            return (ConditionEvaluator._evaluate_logic(left, variables, ctx) and
                    ConditionEvaluator._evaluate_logic(right, variables, ctx))
        if expr.startswith('NOT '):
            sub = expr[4:].strip()
            return not ConditionEvaluator._evaluate_logic(sub, variables, ctx)
        if expr.startswith('(') and expr.endswith(')'):
            return ConditionEvaluator._evaluate_logic(expr[1:-1], variables, ctx)
        return ConditionEvaluator._evaluate_comparison(expr, variables, ctx)

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
    def _evaluate_comparison(cond: str, variables: Dict[str, Any], ctx: Optional['MacroContext'] = None) -> bool:
        cond = cond.replace('##TRUE##', 'True').replace('##FALSE##', 'False')
        for op in ['IS NOT', 'NOT IN']:
            if op in cond:
                left, right = cond.split(op, 1)
                left_val = ConditionEvaluator._cast_value(left.strip(), variables, ctx)
                right_val = ConditionEvaluator._cast_value(right.strip(), variables, ctx)
                if op == 'IS NOT':
                    return left_val is not right_val
                elif op == 'NOT IN':
                    return not ConditionEvaluator._check_in(left_val, right_val)
        for op in ['IS', 'IN']:
            if op in cond:
                left, right = cond.split(op, 1)
                left_val = ConditionEvaluator._cast_value(left.strip(), variables, ctx)
                right_val = ConditionEvaluator._cast_value(right.strip(), variables, ctx)
                if op == 'IS':
                    return left_val is right_val
                elif op == 'IN':
                    return ConditionEvaluator._check_in(left_val, right_val)
        for op in ['==', '!=', '>=', '<=', '>', '<']:
            if op in cond:
                left, right = cond.split(op, 1)
                left_val = ConditionEvaluator._cast_value(left.strip(), variables, ctx)
                right_val = ConditionEvaluator._cast_value(right.strip(), variables, ctx)
                if op == '==': return left_val == right_val
                if op == '!=': return left_val != right_val
                if op == '>': return left_val > right_val
                if op == '<': return left_val < right_val
                if op == '>=': return left_val >= right_val
                if op == '<=': return left_val <= right_val
        val = ConditionEvaluator._cast_value(cond, variables, ctx)
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
    def _cast_value(val: str, variables: Dict[str, Any], ctx: Optional['MacroContext'] = None):
        val = VariableResolver.evaluate_arithmetic(val, variables, ctx=ctx)
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
# 4. Command Pattern
# ==============================
class MacroContext:
    def __init__(self, assistant, delay: float, original_input: Callable, registry: Optional[MacroRegistry] = None):
        self.assistant = assistant
        self.delay = delay
        self.variables: Dict[str, Any] = {}
        self.auto_input = AutoInputHelper(original_input)
        self.functions: Dict[str, Tuple[List[str], Dict[str, str], 'BlockCommand']] = {}
        self.python_namespace = {}
        self.quiet = False
        self.registry = registry or get_registry()   # lưu lại registry để dùng factory

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
    def __init__(self, targets: List[str], value_expr: str):
        self.targets = targets
        self.value_expr = value_expr

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        value = VariableResolver.evaluate_arithmetic(self.value_expr, ctx.variables, ctx=ctx)
        if len(self.targets) == 1 and not self.targets[0].startswith('*'):
            ctx.variables[self.targets[0]] = value
            return None
        if not isinstance(value, (list, tuple)):
            print(f'❌ SET: vế phải {value} không phải list/tuple để unpack')
            return None
        star_index = None
        for i, t in enumerate(self.targets):
            if t.startswith('*'):
                star_index = i
                break
        if star_index is None:
            if len(self.targets) != len(value):
                print(f'❌ SET: cần {len(self.targets)} giá trị, nhưng có {len(value)}')
                return None
            for t, v in zip(self.targets, value):
                ctx.variables[t] = v
        else:
            before = self.targets[:star_index]
            after = self.targets[star_index+1:]
            star_var = self.targets[star_index][1:]
            if len(value) < len(before) + len(after):
                print(f'❌ SET: không đủ giá trị để unpack (cần {len(before)+len(after)}, có {len(value)})')
                return None
            for i, t in enumerate(before):
                ctx.variables[t] = value[i]
            rest_len = len(value) - len(before) - len(after)
            ctx.variables[star_var] = list(value[len(before):len(before)+rest_len])
            for i, t in enumerate(after):
                ctx.variables[t] = value[len(before)+rest_len + i]
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
        if ctx.quiet:
            return None
        msg = self.message.strip()
        msg = VariableResolver.substitute(msg, ctx.variables, ctx=ctx)
        msg = StringUtils.strip_quotes(msg)
        print(f'📢 {msg}')
        return None

class QuestionCommand(MacroCommand):
    def __init__(self, question: str, auto_answer: Optional[str] = None):
        self.question = question
        self.auto_answer = auto_answer

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        q = VariableResolver.substitute(self.question, ctx.variables, ctx=ctx)
        if self.auto_answer is not None:
            ans = VariableResolver.substitute(self.auto_answer, ctx.variables, ctx=ctx)
            ans = StringUtils.strip_quotes(ans)
            if not ctx.quiet:
                print(f'🤖 (tự động) {q}\n👉 {ans}')
            user_input = ans
        else:
            if ctx.quiet:
                user_input = ctx.auto_input.get_input('')
            else:
                user_input = ctx.auto_input.get_input(f'\n🤖 {q}\n👉 ')
        ctx.variables['answer'] = user_input
        if not ctx.quiet:
            print()
        return None

class ReturnCommand(MacroCommand):
    def __init__(self, exprs: List[str]):
        self.exprs = exprs

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        values = [VariableResolver.evaluate_arithmetic(e, ctx.variables, ctx=ctx) for e in self.exprs]
        if len(values) == 1:
            return values[0]
        return tuple(values)

class ImportCommand(MacroCommand):
    def __init__(self, macro_name: str, functions_only: Optional[List[str]] = None):
        self.macro_name = macro_name
        self.functions_only = functions_only

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
        registry = ctx.registry   # dùng registry từ context
        imported_root, imported_functions = registry.macro_parser_class.parse(raw_lines)
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
        sub_ctx = registry.create_context(ctx.assistant, ctx.delay, ctx.auto_input.original_input)
        sub_ctx.variables = ctx.variables.copy()
        sub_ctx.functions = ctx.functions
        sub_ctx.auto_input = ctx.auto_input
        sub_ctx.python_namespace = ctx.python_namespace
        sub_ctx.quiet = ctx.quiet
        if hasattr(ctx, 'import_stack'):
            sub_ctx.import_stack = ctx.import_stack + [self.macro_name]
        else:
            sub_ctx.import_stack = [self.macro_name]
        ret = imported_root.execute(sub_ctx)
        ctx.variables.update(sub_ctx.variables)
        return ret

class RegularCommand(MacroCommand):
    def __init__(self, command_text: str, store_var=None, silent=False):
        self.command_text = command_text
        self.store_var = store_var
        self.silent = silent

    def execute(self, ctx):
        cmd = VariableResolver.substitute(self.command_text, ctx.variables, ctx=ctx)
        if not self.silent and not ctx.quiet:
            print(f'⏩ {cmd}')
        result = ctx.assistant.process_command(cmd)
        if self.store_var:
            ctx.variables[self.store_var] = result
        return None

class PythonCommand(MacroCommand):
    def __init__(self, code: str, store_var: Optional[str] = None, quiet: bool = False):
        self.code = code
        self.store_var = store_var
        self.quiet = quiet

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        resolved = VariableResolver.substitute(self.code, ctx.variables, ctx=ctx)
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
                if not ctx.quiet:
                    print(f"❌ Lỗi PYTHON: {e}")
                return None
        if self.store_var is not None:
            ctx.variables[self.store_var] = result
        elif result is not None and not self.quiet and not ctx.quiet:
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
            if not ctx.quiet:
                print(f"❌ Lỗi PYTHON BLOCK: {e}")
            return None
        if self.store_var is not None:
            if self.store_var in namespace:
                ctx.variables[self.store_var] = namespace[self.store_var]
            else:
                if not ctx.quiet:
                    print(f"⚠️ Biến '{self.store_var}' không tồn tại sau khi chạy PYBLOCK")
        return None

# ---------- Lệnh cấu trúc ----------
class IfCommand(MacroCommand):
    def __init__(self, conditions_blocks: List[Tuple[str, BlockCommand]], else_block: Optional[BlockCommand] = None):
        self.conditions_blocks = conditions_blocks
        self.else_block = else_block

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        for condition, block in self.conditions_blocks:
            if ConditionEvaluator.evaluate(condition, ctx.variables, ctx=ctx):
                return block.execute(ctx)
        if self.else_block:
            return self.else_block.execute(ctx)
        return None

class LoopCommand(MacroCommand):
    def __init__(self, count_expr: str, body: BlockCommand):
        self.count_expr = count_expr
        self.body = body

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        count_str = VariableResolver.evaluate_arithmetic(self.count_expr, ctx.variables, ctx=ctx)
        try:
            count = int(float(count_str))
        except ValueError:
            if not ctx.quiet:
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
    def __init__(self, vars_pattern: List[str], list_expr: str, body: BlockCommand):
        self.vars_pattern = vars_pattern
        self.list_expr = list_expr
        self.body = body
        self.has_star = any(v.startswith('*') for v in vars_pattern)

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        items_value = VariableResolver.evaluate_arithmetic(self.list_expr, ctx.variables, ctx=ctx)
        if isinstance(items_value, (list, tuple, set, range)):
            items = list(items_value)
        elif isinstance(items_value, dict):
            if len(self.vars_pattern) == 2:
                items = list(items_value.items())
            else:
                items = list(items_value.keys())
        elif isinstance(items_value, str):
            items = list(items_value)
        elif hasattr(items_value, '__iter__') and not isinstance(items_value, (type, type(...))):
            try:
                items = list(items_value)
            except:
                print(f'❌ FOREACH: không thể chuyển {type(items_value).__name__} thành list')
                return None
        else:
            if not ctx.quiet:
                print(f'❌ FOREACH: {self.list_expr} không phải iterable (nhận {type(items_value).__name__})')
            return None
        star_index = None
        if self.has_star:
            for i, v in enumerate(self.vars_pattern):
                if v.startswith('*'):
                    star_index = i
                    break
        for item in items:
            try:
                if isinstance(item, (list, tuple)):
                    if self.has_star:
                        before = self.vars_pattern[:star_index]
                        after = self.vars_pattern[star_index+1:]
                        star_var = self.vars_pattern[star_index][1:]
                        if len(item) < len(before) + len(after):
                            raise ValueError(f'Không đủ giá trị để unpack: cần {len(before)+len(after)}, có {len(item)}')
                        for j, var in enumerate(before):
                            ctx.variables[var] = item[j]
                        rest_len = len(item) - len(before) - len(after)
                        ctx.variables[star_var] = list(item[len(before):len(before)+rest_len])
                        for j, var in enumerate(after):
                            ctx.variables[var] = item[len(before)+rest_len + j]
                    else:
                        if len(item) != len(self.vars_pattern):
                            raise ValueError(f'Số biến ({len(self.vars_pattern)}) khác số phần tử ({len(item)})')
                        for var, val in zip(self.vars_pattern, item):
                            ctx.variables[var] = val
                else:
                    if len(self.vars_pattern) == 1:
                        ctx.variables[self.vars_pattern[0]] = item
                    else:
                        raise ValueError(f'Giá trị {item} không thể unpack thành {len(self.vars_pattern)} biến')
                ret = self.body.execute(ctx)
                if ret is not None:
                    return ret
            except BreakException:
                break
            except ContinueException:
                continue
            except Exception as e:
                if not ctx.quiet:
                    print(f'⚠️ FOREACH: {e}')
                continue
        for var in self.vars_pattern:
            vname = var[1:] if var.startswith('*') else var
            if vname in ctx.variables:
                del ctx.variables[vname]
        return None

class WhileCommand(MacroCommand):
    def __init__(self, condition: str, body: BlockCommand):
        self.condition = condition
        self.body = body

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        while ConditionEvaluator.evaluate(self.condition, ctx.variables, ctx=ctx):
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
    def __init__(self, func_name: str, args: List[Tuple[str, str]], kwargs: Dict[str, str], store_var: Optional[str] = None):
        self.func_name = func_name
        self.args = args
        self.kwargs = kwargs
        self.store_var = store_var

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        if self.func_name not in ctx.functions:
            if not ctx.quiet:
                print(f'❌ Hàm không tồn tại: {self.func_name}')
            return None
        func_info = ctx.functions[self.func_name]
        if isinstance(func_info, tuple) and len(func_info) == 3:
            params, defaults, func_body = func_info
        else:
            params, func_body = func_info
            defaults = {}
        actual_args = []
        for typ, expr in self.args:
            if typ == 'pos':
                actual_args.append(VariableResolver.evaluate_arithmetic(expr, ctx.variables, ctx=ctx))
            elif typ == 'star':
                val = VariableResolver.evaluate_arithmetic(expr, ctx.variables, ctx=ctx)
                if isinstance(val, (list, tuple)):
                    actual_args.extend(val)
                else:
                    if not ctx.quiet:
                        print(f'⚠️ *{expr} không phải list/tuple, bỏ qua')
            elif typ == 'starstar':
                val = VariableResolver.evaluate_arithmetic(expr, ctx.variables, ctx=ctx)
                if isinstance(val, dict):
                    for k, v in val.items():
                        self.kwargs[k] = v
                else:
                    if not ctx.quiet:
                        print(f'⚠️ **{expr} không phải dict, bỏ qua')
        kwargs_dict = {}
        for k, expr in self.kwargs.items():
            kwargs_dict[k] = VariableResolver.evaluate_arithmetic(expr, ctx.variables, ctx=ctx)
        arg_map = {}
        for i, arg in enumerate(actual_args):
            if i >= len(params):
                if not ctx.quiet:
                    print(f'❌ Hàm {self.func_name} nhận quá nhiều đối số positional')
                return None
            param_name = params[i]
            arg_map[param_name] = arg
        for k, v in kwargs_dict.items():
            if k not in params:
                if not ctx.quiet:
                    print(f'❌ Hàm {self.func_name} không có tham số {k}')
                return None
            if k in arg_map:
                if not ctx.quiet:
                    print(f'❌ Hàm {self.func_name} nhận đối số {k} hai lần')
                return None
            arg_map[k] = v
        for param in params:
            if param not in arg_map:
                if param in defaults:
                    default_expr = defaults[param]
                    default_val = VariableResolver.evaluate_arithmetic(default_expr, ctx.variables, ctx=ctx)
                    arg_map[param] = default_val
                else:
                    if not ctx.quiet:
                        print(f'❌ Hàm {self.func_name} thiếu đối số bắt buộc: {param}')
                    return None
        sub_ctx = ctx.registry.create_context(ctx.assistant, ctx.delay, ctx.auto_input.original_input)
        sub_ctx.variables = ctx.variables.copy()
        sub_ctx.functions = ctx.functions
        sub_ctx.python_namespace = ctx.python_namespace
        sub_ctx.auto_input = ctx.auto_input
        sub_ctx.quiet = ctx.quiet
        for param, val in arg_map.items():
            sub_ctx.variables[param] = val
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
        resolved = VariableResolver.substitute(self.expr, ctx.variables, ctx=ctx)
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

class AssertCommand(MacroCommand):
    def __init__(self, condition: str, message: Optional[str] = None):
        self.condition = condition
        self.message = message

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        cond = ConditionEvaluator.evaluate(self.condition, ctx.variables, ctx=ctx)
        if not cond:
            msg = self.message if self.message else f"ASSERT thất bại: {self.condition}"
            msg = VariableResolver.substitute(msg, ctx.variables, ctx=ctx)
            msg = StringUtils.strip_quotes(msg)
            raise AssertionFailedError(msg)
        return None

class DelCommand(MacroCommand):
    def __init__(self, var_name: str):
        self.var_name = var_name

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        if self.var_name in ctx.variables:
            del ctx.variables[self.var_name]
        else:
            if not ctx.quiet:
                print(f"⚠️ Biến '{self.var_name}' không tồn tại để xóa")
        return None

class PassCommand(MacroCommand):
    def execute(self, ctx: MacroContext) -> Optional[Any]:
        return None

class QuietCommand(MacroCommand):
    def __init__(self, enable: bool):
        self.enable = enable

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        ctx.quiet = self.enable
        return None

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
            if self.finally_block:
                self.finally_block.execute(ctx)
            raise
        finally:
            if self.finally_block and exc_raised is None:
                self.finally_block.execute(ctx)

class MatchCommand(MacroCommand):
    def __init__(self, value_expr: str, cases: List[Tuple[str, BlockCommand]], default_block: Optional[BlockCommand] = None):
        self.value_expr = value_expr
        self.cases = cases
        self.default_block = default_block

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        value = VariableResolver.evaluate_arithmetic(self.value_expr, ctx.variables, ctx=ctx)
        for pattern, block in self.cases:
            if pattern == '_':
                return block.execute(ctx)
            pat_val = VariableResolver.evaluate_arithmetic(pattern, ctx.variables, ctx=ctx)
            if value == pat_val:
                return block.execute(ctx)
        if self.default_block:
            return self.default_block.execute(ctx)
        return None

class WithCommand(MacroCommand):
    def __init__(self, context_expr: str, as_var: Optional[str], body: BlockCommand):
        self.context_expr = context_expr
        self.as_var = as_var
        self.body = body

    def execute(self, ctx: MacroContext) -> Optional[Any]:
        resolved = VariableResolver.substitute(self.context_expr, ctx.variables, ctx=ctx)
        namespace = ctx.python_namespace
        if '__builtins__' not in namespace:
            namespace['__builtins__'] = __builtins__
        try:
            obj = eval(resolved, namespace, {})
        except Exception as e:
            if not ctx.quiet:
                print(f"❌ Lỗi WITH: không thể tạo context từ '{resolved}' - {e}")
            return None
        try:
            enter_result = obj.__enter__()
        except AttributeError:
            if not ctx.quiet:
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
# 5. Macro Parser (sử dụng registry)
# ==============================
class MacroParser:
    @staticmethod
    def split_args(s: str) -> List[str]:
        parts = []
        current = []
        depth = 0
        for ch in s:
            if ch == ',' and depth == 0:
                parts.append(''.join(current))
                current = []
            else:
                if ch in '([{':
                    depth += 1
                elif ch in ')]}':
                    depth -= 1
                current.append(ch)
        if current:
            parts.append(''.join(current))
        return [p.strip() for p in parts if p.strip()]

    @staticmethod
    def find_block_end(lines: List[str], start: int, end: int,
                       start_prefix: str, end_keyword: str,
                       find_else: bool = False, find_elif: bool = False, find_finally: bool = False) -> Tuple[int, List[Tuple[str, int]]]:
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
    def parse(lines: List[str]) -> Tuple[BlockCommand, Dict[str, Tuple[List[str], Dict[str, str], BlockCommand]]]:
        raw = [line.rstrip('\n') for line in lines]
        functions = {}
        registry = get_registry()
        root_children, _ = MacroParser._parse_sequence(raw, 0, len(raw), functions, registry)
        return BlockCommand(root_children), functions

    @staticmethod
    def _parse_sequence(lines: List[str], start: int, end: int, functions: Dict, registry: MacroRegistry) -> Tuple[List[MacroCommand], int]:
        children = []
        i = start
        while i < end:
            line = lines[i].strip()
            if not line or line.startswith('#'):
                i += 1
                continue
            if line.startswith('FUNCTION '):
                import re
                rest = line[9:].strip()
                match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$', rest)
                if match:
                    func_name = match.group(1)
                    params_str = match.group(2)
                    param_parts = [p.strip() for p in params_str.split(',') if p.strip()]
                    params = []
                    defaults = {}
                    for p in param_parts:
                        if '=' in p:
                            name, default_expr = p.split('=', 1)
                            name = name.strip()
                            default_expr = default_expr.strip()
                            params.append(name)
                            defaults[name] = default_expr
                        else:
                            params.append(p)
                else:
                    func_name = rest
                    params = []
                    defaults = {}
                j, _ = MacroParser.find_block_end(lines, i, end, 'FUNCTION ', 'ENDFUNCTION')
                body_children, _ = MacroParser._parse_sequence(lines, i+1, j, functions, registry)
                functions[func_name] = (params, defaults, BlockCommand(body_children))
                i = j + 1
                continue
            if line == 'ENDFUNCTION':
                i += 1
                continue
            cmd, next_i = MacroParser._parse_command(lines, i, end, functions, registry)
            if cmd is not None:
                children.append(cmd)
            i = next_i
        return children, i

    @staticmethod
    def _parse_command(lines: List[str], pos: int, end: int, functions: Dict, registry: MacroRegistry) -> Tuple[Optional[MacroCommand], int]:
        line = lines[pos].strip()
        if not line:
            return None, pos + 1
        for parser in registry.command_parsers:
            cmd, next_pos = parser(lines, pos, end, functions, registry)
            if cmd is not None:
                return cmd, next_pos
        return None, pos + 1

# ==============================
# 6. Đăng ký các parser (các hàm này nhận thêm registry)
# ==============================
def register_all_parsers(registry: MacroRegistry):
    # IF
    def parse_if(lines, pos, end, functions, registry):
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
                block_children, _ = MacroParser._parse_sequence(lines, current_start, idx, functions, registry)
                conditions_blocks.append((condition, BlockCommand(block_children)))
                condition = elif_cond
                current_start = idx + 1
            elif typ == 'else':
                block_children, _ = MacroParser._parse_sequence(lines, current_start, idx, functions, registry)
                conditions_blocks.append((condition, BlockCommand(block_children)))
                else_children, _ = MacroParser._parse_sequence(lines, idx+1, j, functions, registry)
                if_cmd = registry.if_command_class(conditions_blocks, BlockCommand(else_children))
                return if_cmd, j+1
        block_children, _ = MacroParser._parse_sequence(lines, current_start, j, functions, registry)
        conditions_blocks.append((condition, BlockCommand(block_children)))
        if_cmd = registry.if_command_class(conditions_blocks)
        return if_cmd, j+1
    registry.register_parser(parse_if)

    # LOOP
    def parse_loop(lines, pos, end, functions, registry):
        line = lines[pos].strip()
        if not line.startswith('LOOP '):
            return None, pos
        count_expr = line[5:].strip()
        j, _ = MacroParser.find_block_end(lines, pos, end, 'LOOP ', 'ENDLOOP')
        body_children, _ = MacroParser._parse_sequence(lines, pos+1, j, functions, registry)
        loop_cmd = registry.loop_command_class(count_expr, BlockCommand(body_children))
        return loop_cmd, j+1
    registry.register_parser(parse_loop)

    # FOREACH
    def parse_foreach(lines, pos, end, functions, registry):
        line = lines[pos].strip()
        if not line.startswith('FOREACH '):
            return None, pos
        rest = line[8:].strip()
        if ' IN ' not in rest:
            print(f'❌ Lỗi cú pháp FOREACH: {line}')
            return None, pos+1
        left, right = rest.split(' IN ', 1)
        left = left.strip()
        vars_pattern = [token.strip() for token in left.split(',') if token.strip()]
        list_expr = right.strip()
        j, _ = MacroParser.find_block_end(lines, pos, end, 'FOREACH ', 'ENDFOREACH')
        body_children, _ = MacroParser._parse_sequence(lines, pos+1, j, functions, registry)
        foreach_cmd = registry.foreach_command_class(vars_pattern, list_expr, BlockCommand(body_children))
        return foreach_cmd, j+1
    registry.register_parser(parse_foreach)

    # WHILE
    def parse_while(lines, pos, end, functions, registry):
        line = lines[pos].strip()
        if not line.startswith('WHILE '):
            return None, pos
        condition = line[6:].strip()
        j, _ = MacroParser.find_block_end(lines, pos, end, 'WHILE ', 'ENDWHILE')
        body_children, _ = MacroParser._parse_sequence(lines, pos+1, j, functions, registry)
        while_cmd = registry.while_command_class(condition, BlockCommand(body_children))
        return while_cmd, j+1
    registry.register_parser(parse_while)

    # CALL
    def parse_call(lines, pos, end, functions, registry):
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
        if not match:
            print(f'❌ Cú pháp CALL sai: {call_part}')
            return None, pos+1
        func_name = match.group(1)
        args_str = match.group(2).strip()
        args = []
        kwargs = {}
        tokens = MacroParser.split_args(args_str)
        for t in tokens:
            t = t.strip()
            if t.startswith('**'):
                expr = t[2:].strip()
                args.append(('starstar', expr))
            elif t.startswith('*'):
                expr = t[1:].strip()
                args.append(('star', expr))
            elif '=' in t:
                k, v = t.split('=', 1)
                kwargs[k.strip()] = v.strip()
            else:
                args.append(('pos', t))
        call_cmd = registry.call_command_class(func_name, args, kwargs, store_var)
        return call_cmd, pos+1
    registry.register_parser(parse_call)

    # SET
    def parse_set(lines, pos, end, functions, registry):
        line = lines[pos].strip()
        if not line.startswith('SET '):
            return None, pos
        rest = line[4:].strip()
        if '=' not in rest:
            return None, pos+1
        left, right = rest.split('=', 1)
        left = left.strip()
        targets = [token.strip() for token in left.split(',') if token.strip()]
        value_expr = right.strip()
        set_cmd = registry.set_command_class(targets, value_expr)
        return set_cmd, pos+1
    registry.register_parser(parse_set)

    # INPUT
    def parse_input(lines, pos, end, functions, registry):
        line = lines[pos].strip()
        if not line.startswith('INPUT '):
            return None, pos
        input_cmd = registry.input_command_class(line[6:].strip())
        return input_cmd, pos+1
    registry.register_parser(parse_input)

    # PRINT
    def parse_print(lines, pos, end, functions, registry):
        line = lines[pos].strip()
        if not line.startswith('PRINT '):
            return None, pos
        print_cmd = registry.print_command_class(line[6:].strip())
        return print_cmd, pos+1
    registry.register_parser(parse_print)

    # QUESTION
    def parse_question(lines, pos, end, functions, registry):
        line = lines[pos].strip()
        if not line.startswith('? '):
            return None, pos
        rest = line[2:].strip()
        auto = None
        if ' auto:' in rest:
            q, a = rest.split(' auto:', 1)
            auto = a.strip()
            rest = q.strip()
        q_cmd = registry.question_command_class(rest, auto)
        return q_cmd, pos+1
    registry.register_parser(parse_question)

    # RETURN
    def parse_return(lines, pos, end, functions, registry):
        line = lines[pos].strip()
        if not line.startswith('RETURN '):
            return None, pos
        rest = line[7:].strip()
        exprs = MacroParser.split_args(rest)
        return_cmd = registry.return_command_class(exprs)
        return return_cmd, pos+1
    registry.register_parser(parse_return)

    # IMPORT
    def parse_import(lines, pos, end, functions, registry):
        line = lines[pos].strip()
        if line.startswith('IMPORT '):
            macro_name = line[7:].strip()
            if not macro_name:
                print('❌ Cú pháp: IMPORT <tên_macro>')
                return None, pos+1
            import_cmd = registry.import_command_class(macro_name)
            return import_cmd, pos+1
        return None, pos
    registry.register_parser(parse_import)

    # FROM IMPORT
    def parse_from_import(lines, pos, end, functions, registry):
        line = lines[pos].strip()
        if not line.startswith('FROM '):
            return None, pos
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
        import_cmd = registry.import_command_class(macro_name, functions_only=func_names)
        return import_cmd, pos+1
    registry.register_parser(parse_from_import)

    # PYTHON
    def parse_python(lines, pos, end, functions, registry):
        line = lines[pos].strip()
        if not line.startswith('PYTHON '):
            return None, pos
        rest = line[7:].strip()
        quiet = False
        if rest.startswith('QUIET '):
            quiet = True
            rest = rest[6:].strip()
        store_var = None
        if ' -> ' in rest:
            expr, var = rest.split(' -> ', 1)
            store_var = var.strip()
            rest = expr.strip()
        py_cmd = registry.python_command_class(rest, store_var, quiet)
        return py_cmd, pos+1
    registry.register_parser(parse_python)

    # PYBLOCK
    def parse_pyblock(lines, pos, end, functions, registry):
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
        pyblock_cmd = registry.python_block_command_class(code, store_var)
        return pyblock_cmd, j+1
    registry.register_parser(parse_pyblock)

    # BREAK
    def parse_break(lines, pos, end, functions, registry):
        line = lines[pos].strip()
        if line == 'BREAK':
            return registry.break_command_class(), pos+1
        return None, pos
    registry.register_parser(parse_break)

    # CONTINUE
    def parse_continue(lines, pos, end, functions, registry):
        line = lines[pos].strip()
        if line == 'CONTINUE':
            return registry.continue_command_class(), pos+1
        return None, pos
    registry.register_parser(parse_continue)

    # TRY
    def parse_try(lines, pos, end, functions, registry):
        line = lines[pos].strip()
        if line != 'TRY':
            return None, pos
        j, extra = MacroParser.find_block_end(lines, pos, end, 'TRY', 'ENDTRY', find_finally=True)
        catches = []
        finally_block = None
        blocks_info = []
        i = pos + 1
        while i < j:
            curr = lines[i].strip()
            if curr.startswith('EXCEPT'):
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
        try_end = pos + 1
        except_starts = [idx for typ, idx, _ in blocks_info if typ == 'except']
        if except_starts:
            try_end = except_starts[0]
        elif any(typ == 'finally' for typ, _, _ in blocks_info):
            finally_start = next(idx for typ, idx, _ in blocks_info if typ == 'finally')
            try_end = finally_start
        else:
            try_end = j
        try_children, _ = MacroParser._parse_sequence(lines, pos+1, try_end, functions, registry)
        try_block = BlockCommand(try_children)
        for typ, start, end_block in blocks_info:
            if typ == 'except':
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
                body_children, _ = MacroParser._parse_sequence(lines, start+1, end_block, functions, registry)
                catches.append((exc_type, var_name, BlockCommand(body_children)))
            elif typ == 'finally':
                body_children, _ = MacroParser._parse_sequence(lines, start+1, end_block, functions, registry)
                finally_block = BlockCommand(body_children)
        try_cmd = registry.try_command_class(try_block, catches, finally_block)
        return try_cmd, j+1
    registry.register_parser(parse_try)

    # MATCH
    def parse_match(lines, pos, end, functions, registry):
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
                body_children, _ = MacroParser._parse_sequence(lines, current+1, next_case, functions, registry)
                cases.append((pattern, BlockCommand(body_children)))
                current = next_case
            elif curr_line.startswith('DEFAULT'):
                next_default = current + 1
                while next_default < j:
                    if lines[next_default].strip().startswith('CASE ') or lines[next_default].strip() == 'ENDMATCH':
                        break
                    next_default += 1
                body_children, _ = MacroParser._parse_sequence(lines, current+1, next_default, functions, registry)
                default_block = BlockCommand(body_children)
                current = next_default
            else:
                current += 1
        match_cmd = registry.match_command_class(value_expr, cases, default_block)
        return match_cmd, j+1
    registry.register_parser(parse_match)

    # WITH
    def parse_with(lines, pos, end, functions, registry):
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
        body_children, _ = MacroParser._parse_sequence(lines, pos+1, j, functions, registry)
        with_cmd = registry.with_command_class(context_expr, as_var, BlockCommand(body_children))
        return with_cmd, j+1
    registry.register_parser(parse_with)

    # RAISE
    def parse_raise(lines, pos, end, functions, registry):
        line = lines[pos].strip()
        if not line.startswith('RAISE '):
            return None, pos
        expr = line[6:].strip()
        if not expr:
            print('❌ Cú pháp: RAISE <exception_expression>')
            return None, pos+1
        raise_cmd = registry.raise_command_class(expr)
        return raise_cmd, pos+1
    registry.register_parser(parse_raise)

    # ASSERT
    def parse_assert(lines, pos, end, functions, registry):
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
        assert_cmd = registry.assert_command_class(condition, message)
        return assert_cmd, pos+1
    registry.register_parser(parse_assert)

    # DEL
    def parse_del(lines, pos, end, functions, registry):
        line = lines[pos].strip()
        if not line.startswith('DEL '):
            return None, pos
        var_name = line[4:].strip()
        if not var_name:
            print('❌ Cú pháp: DEL <tên_biến>')
            return None, pos+1
        del_cmd = registry.del_command_class(var_name)
        return del_cmd, pos+1
    registry.register_parser(parse_del)

    # PASS
    def parse_pass(lines, pos, end, functions, registry):
        line = lines[pos].strip()
        if line == 'PASS':
            return registry.pass_command_class(), pos+1
        return None, pos
    registry.register_parser(parse_pass)

    # QUIET
    def parse_quiet(lines, pos, end, functions, registry):
        line = lines[pos].strip()
        if line == 'QUIET ON':
            return registry.quiet_command_class(True), pos+1
        if line == 'QUIET OFF':
            return registry.quiet_command_class(False), pos+1
        return None, pos
    registry.register_parser(parse_quiet)

    # SILENT (regular command with silent flag)
    def parse_silent(lines, pos, end, functions, registry):
        line = lines[pos].strip()
        if not line.startswith('SILENT '):
            return None, pos
        inner_line = line[7:].strip()
        if ' -> ' in inner_line:
            cmd, var = inner_line.split(' -> ', 1)
            return registry.regular_command_class(cmd.strip(), var.strip(), silent=True), pos+1
        return registry.regular_command_class(inner_line, silent=True), pos+1
    registry.register_parser(parse_silent)

    # REGULAR (fallback)
    def parse_regular(lines, pos, end, functions, registry):
        line = lines[pos].strip()
        if line.startswith(('FUNCTION ', 'IF ', 'LOOP ', 'FOREACH ', 'WHILE ', 'CALL ', 'SET ', 'INPUT ', 'PRINT ', '? ', 'RETURN ', 'IMPORT ', 'FROM ', 'PYTHON ', 'PYBLOCK ', 'BREAK', 'CONTINUE', 'TRY', 'MATCH ', 'WITH ', 'RAISE ', 'ASSERT ', 'DEL ', 'PASS', 'QUIET ', 'SILENT ')):
            return None, pos
        if ' -> ' in line:
            cmd, var = line.split(' -> ', 1)
            return registry.regular_command_class(cmd.strip(), var.strip()), pos+1
        return registry.regular_command_class(line), pos+1
    registry.register_parser(parse_regular)

# ==============================
# 7. Gán class mặc định vào registry (sau khi tất cả class đã được định nghĩa)
# ==============================
def setup_default_registry(registry: MacroRegistry):
    registry.set_command_class = SetCommand
    registry.input_command_class = InputCommand
    registry.print_command_class = PrintCommand
    registry.question_command_class = QuestionCommand
    registry.return_command_class = ReturnCommand
    registry.import_command_class = ImportCommand
    registry.regular_command_class = RegularCommand
    registry.python_command_class = PythonCommand
    registry.python_block_command_class = PythonBlockCommand
    registry.if_command_class = IfCommand
    registry.loop_command_class = LoopCommand
    registry.foreach_command_class = ForeachCommand
    registry.while_command_class = WhileCommand
    registry.call_command_class = CallCommand
    registry.break_command_class = BreakCommand
    registry.continue_command_class = ContinueCommand
    registry.raise_command_class = RaiseCommand
    registry.assert_command_class = AssertCommand
    registry.del_command_class = DelCommand
    registry.pass_command_class = PassCommand
    registry.quiet_command_class = QuietCommand
    registry.try_command_class = TryCommand
    registry.match_command_class = MatchCommand
    registry.with_command_class = WithCommand

    registry.string_utils_class = StringUtils
    registry.variable_resolver_class = VariableResolver
    registry.condition_evaluator_class = ConditionEvaluator
    registry.auto_input_helper_class = AutoInputHelper

    registry.macro_parser_class = MacroParser
    registry.macro_context_class = MacroContext
    registry.macro_executor_class = MacroExecutor
    registry.macro_command_handler_class = MacroCommandHandler

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
            delay = 0.1
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
        registry = get_registry()
        root_command, functions = registry.macro_parser_class.parse(raw_lines)
        ctx = registry.create_context(self.assistant, delay, builtins.input)
        ctx.functions = functions
        executor = registry.create_executor(ctx)
        executor.execute(root_command)

# ==============================
# 10. Khởi tạo registry mặc định (sau khi tất cả class đã có)
# ==============================
setup_default_registry(_global_registry)
# Đăng ký tất cả parser (cần registry đã có các class)
register_all_parsers(_global_registry)

# ==============================
# 11. Plugin info
# ==============================
plugin_info = {
    'enabled': True,
    'register': lambda assistant: assistant.handlers.append(MacroCommandHandler(assistant)),
    'methods': [],
    'classes': [MacroRecorder, MacroCommandHandler],
    'description': 'Ghi và chạy macro với IF/ELIF/ELSE, LOOP, FOREACH (hỗ trợ unpack), WHILE, FUNCTION/CALL (hỗ trợ *args, **kwargs và tham số mặc định), INPUT, SET (hỗ trợ unpack gán), ?, PRINT, IMPORT, FROM IMPORT, PYTHON, BREAK, CONTINUE, TRY/FINALLY/EXCEPT, MATCH/CASE, WITH, ASSERT, DEL, PASS, RAISE, RETURN nhiều giá trị, QUIET ON/OFF (im lặng toàn cục) - CÚ PHÁP BIẾN $ (ví dụ $ten, ${biểu thức}) thay vì {} - **OCP Complete: mọi thành phần (kể cả MacroContext) đều có thể ghi đè qua MacroRegistry**'
  }
