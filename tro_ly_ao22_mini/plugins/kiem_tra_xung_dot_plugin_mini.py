class ConflictWatcherPlugin:

    def __init__(self, assistant):
        self.assistant = assistant
        self.original_process_command = assistant.process_command
        self.monkey_patch_process_command()

    def monkey_patch_process_command(self):

        def wrapped_process_command(command: str) ->bool:
            command = command.strip().lower()
            handlers = self.assistant.handlers
            capable = [h for h in handlers if h != self and hasattr(h,
                'can_handle') and callable(h.can_handle) and h.can_handle(
                command)]
            if len(capable) > 1:
                print(
                    f"⚠️ Có {len(capable)} plugin có thể xử lý lệnh '{command}':"
                    )
                for i, h in enumerate(capable):
                    print(
                        f"   {i + 1}. {getattr(h, '__name__', h.__class__.__name__)}"
                        )
                print('⚠️ Chỉ plugin đầu tiên trong danh sách được sử dụng.\n')
            return self.original_process_command(command)
        self.assistant.process_command = wrapped_process_command

    def can_handle(self, command: str) ->bool:
        return False

    def handle(self, command: str):
        pass


def register(assistant):
    assistant.handlers.insert(0, ConflictWatcherPlugin(assistant))


plugin_info = {'name': 'ConflictWatcherPlugin', 'enabled': True, 'register':
    register}
