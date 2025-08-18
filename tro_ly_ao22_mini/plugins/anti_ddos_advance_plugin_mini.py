import time
from collections import defaultdict
from typing import Any
SAFE_COMMANDS = ['help', 'exit', 'quit']


class RateLimiter:

    def __init__(self):
        self.attempts = defaultdict(list)
        self.max_attempts = 20
        self.time_window = 10

    def check_limit(self, identifier: str) ->(bool, float):
        now = time.time()
        self.attempts[identifier] = [t for t in self.attempts[identifier] if
            now - t < self.time_window]
        if len(self.attempts[identifier]) >= self.max_attempts:
            oldest = self.attempts[identifier][0]
            time_left = self.time_window - (now - oldest)
            return False, time_left
        self.attempts[identifier].append(now)
        return True, 0.0


def register(assistant: Any) ->None:
    assistant.rate_limiter = RateLimiter()
    original_process = assistant.process_command

    def rate_limited_process(command: str) ->bool:
        if command.strip().lower() in SAFE_COMMANDS:
            return original_process(command)
        user_id = 'default_user'
        allowed, wait_time = assistant.rate_limiter.check_limit(user_id)
        if not allowed:
            print(
                f'⏳ Bạn đã vượt quá giới hạn. Vui lòng thử lại sau {wait_time:.1f} giây...'
                )
            return True
        return original_process(command)
    assistant.process_command = rate_limited_process


plugin_info = {'enabled': False, 'register': register}
