import threading
import time


class DDoSSimulatorPlugin:

    def __init__(self, assistant):
        self.assistant = assistant
        self.running = False

    def can_handle(self, command: str) ->bool:
        return command == 'simulate ddos'

    def handle(self, command: str) ->None:
        if self.running:
            print('🚫 Đang mô phỏng DDoS rồi.')
            return
        print('⚠️ Bắt đầu mô phỏng gửi 10 lệnh/giây trong 5 giây...')
        self.running = True
        thread = threading.Thread(target=self.simulate_requests)
        thread.start()

    def simulate_requests(self):
        start_time = time.time()
        duration = 5
        commands_per_second = 10
        interval = 1.0 / commands_per_second
        total_sent = 0
        while time.time() - start_time < duration:
            self.assistant.process_command('111 ế ẩm')
            total_sent += 1
            time.sleep(interval)
        print(f'✅ Mô phỏng hoàn tất. Tổng cộng đã gửi {total_sent} lệnh.')
        self.running = False


plugin_info = {'enabled': False, 'command_handle': ['simulate ddos'],
    'register': lambda assistant: assistant.handlers.append(
    DDoSSimulatorPlugin(assistant))}
