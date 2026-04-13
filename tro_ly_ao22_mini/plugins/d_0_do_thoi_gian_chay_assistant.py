import time
import functools
_START_TIME = time.perf_counter()


def register(assistant):
    """
    Hàm được gọi khi plugin được tải.
    Thay thế phương thức run() của assistant để chèn đo thời gian.
    """
    original_run = assistant.run

    @functools.wraps(original_run)
    def timed_run():
        elapsed_ms = (time.perf_counter() - _START_TIME) * 1000
        print('🤖 Xin chào, tôi là trợ lý ảo (Asi-86)')
        print(f'⏱️ Khởi động hoàn tất trong {elapsed_ms:.2f} ms')
        print("Nhập 'exit' để thoát. \n")
        while True:
            try:
                user_input = input('Bạn: ')
                if not assistant.process_command(user_input):
                    break
            except KeyboardInterrupt:
                print('\n👋 Tạm biệt!')
                break
            except Exception as e:
                print(f'⚠️ Lỗi: {e}')
    assistant.run = timed_run


plugin_info = {'enabled': True, 'register': register}
