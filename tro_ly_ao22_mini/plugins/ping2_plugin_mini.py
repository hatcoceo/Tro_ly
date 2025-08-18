import time


class PingPlugin:

    def __init__(self, assistant):
        self.assistant = assistant
        self.ping_count = 0
        self.log_file = 'ping_log.txt'

    def can_handle(self, command: str) ->bool:
        return command.strip().lower() == 'ping'

    def handle(self, command: str) ->None:
        start_time = time.time()
        response_time = (time.time() - start_time) * 1000
        self.ping_count += 1
        message = (
            f'🏓 Pong! (Lần ping thứ {self.ping_count}, phản hồi: {response_time:.2f}ms)'
            )
        print(message)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")


plugin_info = {'enabled': False, 'command_handle': ['ping'], 'register': lambda
    assistant: assistant.handlers.append(PingPlugin(assistant))}
