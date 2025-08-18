import os
import shutil


class FolderManagerPlugin:

    def can_handle(self, command: str) ->bool:
        commands = ['tạo thư mục', 'xóa thư mục', 'đổi tên thư mục',
            'copy thư mục']
        return any(command.startswith(cmd) for cmd in commands)

    def handle(self, command: str) ->None:
        try:
            if command.startswith('tạo thư mục'):
                folder_name = command.replace('tạo thư mục', '').strip()
                if not folder_name:
                    print('⚠️ Bạn cần nhập tên thư mục.')
                    return
                os.makedirs(folder_name, exist_ok=True)
                print(f'📁 Đã tạo thư mục: {folder_name}')
            elif command.startswith('xóa thư mục'):
                folder_name = command.replace('xóa thư mục', '').strip()
                if not folder_name:
                    print('⚠️ Bạn cần nhập tên thư mục.')
                    return
                if os.path.exists(folder_name) and os.path.isdir(folder_name):
                    shutil.rmtree(folder_name)
                    print(f'🗑️ Đã xóa thư mục: {folder_name}')
                else:
                    print('❌ Thư mục không tồn tại.')
            elif command.startswith('đổi tên thư mục'):
                parts = command.replace('đổi tên thư mục', '').strip().split()
                if len(parts) < 2:
                    print(
                        '⚠️ Cú pháp: đổi tên thư mục <thư_mục_cũ> <thư_mục_mới>'
                        )
                    return
                old_name, new_name = parts[0], parts[1]
                if os.path.exists(old_name) and os.path.isdir(old_name):
                    os.rename(old_name, new_name)
                    print(f'✏️ Đã đổi tên thư mục {old_name} thành {new_name}')
                else:
                    print('❌ Thư mục không tồn tại.')
            elif command.startswith('copy thư mục'):
                parts = command.replace('copy thư mục', '').strip().split()
                if len(parts) < 2:
                    print(
                        '⚠️ Cú pháp: copy thư mục <thư_mục_nguồn> <thư_mục_đích>'
                        )
                    return
                src, dest = parts[0], parts[1]
                if os.path.exists(src) and os.path.isdir(src):
                    shutil.copytree(src, dest, dirs_exist_ok=True)
                    print(f'📂 Đã copy thư mục {src} sang {dest}')
                else:
                    print('❌ Thư mục nguồn không tồn tại.')
        except Exception as e:
            print(f'⚠️ Lỗi khi thao tác thư mục: {e}')


def register(assistant):
    assistant.handlers.append(FolderManagerPlugin())


plugin_info = {'enabled': True, 'register': register, 'command_handle': [
    'tạo thư mục', 'xóa thư mục', 'đổi tên thư mục', 'copy thư mục']}
