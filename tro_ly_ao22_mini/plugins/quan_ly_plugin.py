import os
import sys


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

    def restart_program(self):
        """Khởi động lại tiến trình Python"""
        print('🔄 Đang khởi động lại để áp dụng thay đổi...')
        python = sys.executable
        os.execv(python, [python] + sys.argv)

    def get_plugin_list(self):
        """Trả về danh sách plugin hợp lệ (bỏ qua file ẩn và file manager)"""
        plugin_list = [f[:-3] for f in os.listdir(self.plugins_folder) if f
            .endswith('.py') and not f.startswith('_') and f !=
            'plugin_manager.py']
        return sorted(plugin_list)

    def resolve_plugin_name(self, name_or_index):
        """Nếu nhập số thứ tự thì đổi sang tên plugin"""
        plugin_list = self.get_plugin_list()
        if name_or_index.isdigit():
            idx = int(name_or_index) - 1
            if 0 <= idx < len(plugin_list):
                return plugin_list[idx]
            else:
                print('⚠️ Số thứ tự plugin không hợp lệ.')
                return None
        return name_or_index

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
                name = input(' Tên hoặc số thứ tự plugin mới: ').strip()
                self.create_plugin(f'tạo plugin {name}')
            elif choice == '2':
                name = input('✏️ Tên hoặc số thứ tự plugin cần sửa: ').strip()
                self.edit_plugin(f'sửa plugin {name}')
            elif choice == '3':
                name = input('️ Tên hoặc số thứ tự plugin cần xóa: ').strip()
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
            print('\n📦 Danh sách plugin:')
            plugin_list = self.get_plugin_list()
            if not plugin_list:
                print(' (trống)')
                return
            for idx, name in enumerate(plugin_list, start=1):
                print(f'{idx}. {name}')
        except Exception as e:
            print(f'⚠️ Lỗi khi liệt kê plugin: {e}')

    def create_plugin(self, command: str) ->None:
        try:
            name = command.replace('tạo plugin', '').strip()
            if not name:
                print('⚠️ Bạn cần nhập tên hoặc số thứ tự plugin.')
                return
            if name.isdigit():
                print(
                    '⚠️ Không thể tạo plugin bằng số thứ tự, vui lòng nhập tên.'
                    )
                return
            filename = f'{self.plugins_folder}/{name}.py'
            if os.path.exists(filename):
                print(f"⚠️ Plugin '{name}' đã tồn tại.")
                return
            class_name = f'{name.capitalize()}Plugin'
            template = f'# Plugin mẫu\n\nclass {class_name}:\n    pass\n'
            with open(filename, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(template)
            print(f"✅ Plugin '{name}' đã được tạo.")
            self.restart_program()
        except Exception as e:
            print(f'⚠️ Lỗi khi tạo plugin: {e}')

    def edit_plugin(self, command: str) ->None:
        try:
            name_or_index = command.replace('sửa plugin', '').strip()
            if not name_or_index:
                print('⚠️ Bạn cần nhập tên hoặc số thứ tự plugin.')
                return
            name = self.resolve_plugin_name(name_or_index)
            if not name:
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
            self.restart_program()
        except Exception as e:
            print(f'⚠️ Lỗi khi sửa plugin: {e}')

    def delete_plugin(self, command: str) ->None:
        try:
            name_or_index = command.replace('xóa plugin', '').strip()
            if not name_or_index:
                print('⚠️ Bạn cần nhập tên hoặc số thứ tự plugin.')
                return
            name = self.resolve_plugin_name(name_or_index)
            if not name:
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
            self.restart_program()
        except Exception as e:
            print(f'⚠️ Lỗi khi xóa plugin: {e}')


def register(assistant):
    assistant.handlers.insert(1, PluginManager(assistant))


plugin_info = {'name': 'plugin_manager', 'enabled': True, 'register':
    register, 'command_handle': ['quản lý plugin', 'tạo plugin',
    'sửa plugin', 'xóa plugin']}
