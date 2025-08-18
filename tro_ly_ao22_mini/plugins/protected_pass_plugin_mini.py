import getpass


def register(assistant):
    password = 'admin123'
    for _ in range(3):
        entered = getpass.getpass('🔐 Nhập mật khẩu để sử dụng trợ lý: ')
        if entered == password:
            print('✅ Đăng nhập thành công.')
            return
        else:
            print('❌ Sai mật khẩu.')
    print('🚫 Truy cập bị từ chối.')
    exit(1)


plugin_info = {'enabled': False, 'register': register, 'command_handle': None}
