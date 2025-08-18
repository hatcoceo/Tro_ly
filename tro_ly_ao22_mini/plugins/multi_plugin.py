class HelloHandler:

    def can_handle(self, command):
        return command == 'hello'

    def handle(self, command):
        print('Xin chào từ multi plugin !')


class ByeHandler:

    def can_handle(self, command):
        return command == 'bye'

    def handle(self, command):
        print('Tạm biệt từ multi plugin ')


def register(assistant):
    assistant.handlers.append(HelloHandler())
    assistant.handlers.append(ByeHandler())


plugin_info = {'enabled': False, 'register': register}
