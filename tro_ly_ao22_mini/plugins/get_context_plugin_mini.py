class GetContextPlugin:

    def can_handle(self, command: str) ->bool:
        return command == 'get context'

    def handle(self, command: str) ->None:
        from pprint import pprint
        print('📦 Current assistant context:')
        pprint(self.assistant.context)

    def __init__(self, assistant):
        self.assistant = assistant


plugin_info = {'enabled': True, 'command_handle': ['get context'],
    'register': lambda assistant: assistant.handlers.append(
    GetContextPlugin(assistant))}
