import os


class PluginManager:

    def __init__(self, assistant):
        self.assistant = assistant
        self.plugins_folder = 'plugins'

    def can_handle(self, command: str) ->bool:
        return command in ['quản lý plugin', 'tạo plugin', 'sửa plugin',
            'xóa plugin'] or any(command.startswith(prefix) for prefix in [
            'tạo plugin', 'sửa plugin', 'xóa plugin'])

    def handle(self, command: str) ->None:
        if command == 'quản lý plugin':
            self.menu()
        elif command.startswith('tạo plugin'):
            self.create_plugin(command)
        elif command.startswith('sửa plugin'):
            self.edit_plugin(command)
        elif command.startswith('xóa plugin'):
            self.delete_plugin(command)

    def menu(self):
        while True:
            print('\n️ Quản lý Plugin')
            print('1. Tạo plugin')
            print('2. Sửa plugin')
            print('3. Xóa plugin')
            print('4. Danh sách plugin')
            print('5. Thoát menu')
            choice = input(' Nhập lựa chọn của bạn: ').strip()
            if choice == '1':
                name = input(' Tên plugin mới: ').strip()
                self.create_plugin(f'tạo plugin {name}')
            elif choice == '2':
                name = input('✏️ Tên plugin cần sửa: ').strip()
                self.edit_plugin(f'sửa plugin {name}')
            elif choice == '3':
                name = input('️ Tên plugin cần xóa: ').strip()
                self.delete_plugin(f'xóa plugin {name}')
            elif choice == '4':
                self.list_plugins()
            elif choice == '5':
                print(' Thoát menu plugin.')
                break
            else:
                print('⚠️ Lựa chọn không hợp lệ.')

    def list_plugins(self):
        try:
            print('\n Danh sách plugin:')
            files = [f for f in os.listdir(self.plugins_folder) if f.
                endswith('.py')]
            if not files:
                print(' (trống)')
            for f in files:
                print(' -', f[:-3])
        except Exception as e:
            print(f'⚠️ Lỗi khi liệt kê plugin: {e}')

    def create_plugin(self, command: str) ->None:
        try:
            name = command.replace('tạo plugin', '').strip()
            if not name:
                print('⚠️ Bạn cần nhập tên plugin.')
                return
            filename = f'{self.plugins_folder}/{name}.py'
            if os.path.exists(filename):
                print(f"⚠️ Plugin '{name}' đã tồn tại.")
                return
            class_name = f'{name.capitalize()}Plugin'
            template = f' '
            with open(filename, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(template)
            print(f"✅ Plugin '{name}' đã được tạo.")
        except Exception as e:
            print(f'⚠️ Lỗi khi tạo plugin: {e}')

    def edit_plugin(self, command: str) ->None:
        try:
            name = command.replace('sửa plugin', '').strip()
            if not name:
                print('⚠️ Bạn cần nhập tên plugin.')
                return
            filename = f'{self.plugins_folder}/{name}.py'
            if not os.path.exists(filename):
                print(f"⚠️ Plugin '{name}' không tồn tại.")
                return
            print(f"\n Nội dung hiện tại của plugin '{name}':\n")
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                print(f.read())
            print(
                '\n✏️ Nhập nội dung mới cho plugin (kết thúc bằng một dòng chứa `EOF`):'
                )
            new_lines = []
            while True:
                line = input()
                if line.strip() == 'EOF':
                    break
                new_lines.append(line)
            with open(filename, 'w', encoding='utf-8', errors='ignore') as f:
                f.write('\n'.join(new_lines))
            print(f"✅ Plugin '{name}' đã được cập nhật.")
        except Exception as e:
            print(f'⚠️ Lỗi khi sửa plugin: {e}')

    def delete_plugin(self, command: str) ->None:
        try:
            name = command.replace('xóa plugin', '').strip()
            if not name:
                print('⚠️ Bạn cần nhập tên plugin.')
                return
            filename = f'{self.plugins_folder}/{name}.py'
            if not os.path.exists(filename):
                print(f"⚠️ Plugin '{name}' không tồn tại.")
                return
            confirm = input(
                f"❓ Bạn chắc chắn muốn xóa plugin '{name}'? (y/n): ").strip(
                ).lower()
            if confirm != 'y':
                print('❌ Hủy xóa.')
                return
            os.remove(filename)
            print(f"️✅ Plugin '{name}' đã bị xóa.")
        except Exception as e:
            print(f'⚠️ Lỗi khi xóa plugin: {e}')


def register(assistant):
    assistant.handlers.insert(1, PluginManager(assistant))


plugin_info = {'name': 'plugin_manager', 'enabled': False, 'register':
    register, 'command_handle': ['xem mã plugin', 'tạo plugin',
    'sửa plugin', 'xóa plugin']}
