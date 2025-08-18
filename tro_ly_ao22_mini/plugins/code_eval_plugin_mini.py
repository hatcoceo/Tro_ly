plugin_info = {'enabled': False, 'register': lambda assistant: assistant.
    handlers.append(CodeEvalHandler())}


class CodeEvalHandler:

    def can_handle(self, command: str) ->bool:
        return command.startswith('eval ')

    def handle(self, command: str) ->None:
        code = command[len('eval '):]
        try:
            result = eval(code)
            if result is not None:
                print(f'📥 Kết quả: {result}')
        except Exception as e:
            print(f'⚠️ Lỗi khi chạy eval: {e}')
