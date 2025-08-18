class ConfigHandler:

    def __init__(self, assistant):
        self.assistant = assistant
        self.assistant.context.setdefault('case_sensitive', False)

    def can_handle(self, command: str) ->bool:
        return command.startswith('config ')

    def handle(self, command: str) ->None:
        parts = command.split(maxsplit=2)
        if len(parts) < 3:
            print('⚙️ Cú pháp: config case_sensitive on/off')
            return
        setting, value = parts[1], parts[2].lower()
        if setting == 'case_sensitive':
            if value in ['on', 'true', '1']:
                self.assistant.context['case_sensitive'] = True
                print('🔠 Chế độ phân biệt chữ hoa/thường: BẬT')
            elif value in ['off', 'false', '0']:
                self.assistant.context['case_sensitive'] = False
                print('🔡 Chế độ phân biệt chữ hoa/thường: TẮT')
            else:
                print('⚠️ Giá trị không hợp lệ! Dùng on/off')
        else:
            print('⚠️ Cấu hình không hỗ trợ:', setting)


def register(assistant):
    handler = ConfigHandler(assistant)
    assistant.handlers.append(handler)

    def new_process_command(command: str) ->bool:
        if not assistant.context.get('case_sensitive', False):
            command = command.strip().lower()
        else:
            command = command.strip()
        if command in ['exit', 'quit', 'thoát']:
            print('👋 Goodbye!')
            return False
        for h in assistant.handlers:
            if hasattr(h, 'can_handle') and h.can_handle(command):
                if hasattr(h, 'handle'):
                    h.handle(command)
                    return True
        print("🤷 I don't understand that command")
        return True
    assistant.process_command = new_process_command


plugin_info = {'enabled': False, 'register': register, 'command_handle': [
    'config case_sensitive on', 'config case_sensitive off']}
