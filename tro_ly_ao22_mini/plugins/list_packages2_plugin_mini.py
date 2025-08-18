import pkg_resources
import importlib
import inspect


class PackageInspector:

    def can_handle(self, command: str) ->bool:
        return command.startswith('xem thư viện ') or command.startswith(
            'xem mã ') or command == 'xem tất cả thư viện'

    def handle(self, command: str) ->None:
        if command == 'xem tất cả thư viện':
            self.inspect_all_packages()
        elif command.startswith('xem thư viện '):
            package_name = command.replace('xem thư viện ', '').strip()
            self.inspect_package(package_name)
        elif command.startswith('xem mã '):
            parts = command.replace('xem mã ', '').strip().split(' trong ')
            if len(parts) == 2:
                name, package_name = parts
                self.show_source(package_name.strip(), name.strip())
            else:
                print(
                    '⚠️ Cú pháp không hợp lệ. Dùng: xem mã <hàm|class> trong <thư viện>'
                    )

    def inspect_all_packages(self):
        print('🔍 Đang liệt kê tất cả hàm và class của các thư viện:')
        packages = sorted([d.project_name for d in pkg_resources.working_set])
        for pkg in packages:
            print(f'\n📦 {pkg}')
            self.inspect_package(pkg, silent_errors=True)

    def inspect_package(self, package_name: str, silent_errors=False):
        try:
            module = importlib.import_module(package_name)
            functions = inspect.getmembers(module, inspect.isfunction)
            classes = inspect.getmembers(module, inspect.isclass)
            if not functions and not classes:
                print('   (Không tìm thấy hàm hoặc class nào)')
                return
            if functions:
                print('  🛠️  Hàm:')
                for idx, (name, _) in enumerate(functions, 1):
                    print(
                        f'     {idx:3}. {name}    👉 xem mã {name} trong {package_name}'
                        )
            if classes:
                print('  🧱 Class:')
                for idx, (name, _) in enumerate(classes, 1):
                    print(
                        f'     {idx:3}. {name}    👉 xem mã {name} trong {package_name}'
                        )
        except Exception as e:
            if not silent_errors:
                print(
                    f"⚠️ Không thể nhập hoặc phân tích thư viện '{package_name}': {e}"
                    )
            else:
                print('   ⚠️ Không thể phân tích.')

    def show_source(self, package_name: str, name: str):
        try:
            module = importlib.import_module(package_name)
            member = getattr(module, name, None)
            if member is None:
                print(f"⚠️ Không tìm thấy '{name}' trong '{package_name}'")
                return
            source = inspect.getsource(member)
            print(f'📄 Mã nguồn của {name} trong {package_name}:\n')
            print(source)
        except Exception as e:
            print(f'⚠️ Không thể hiển thị mã nguồn: {e}')


def register(assistant):
    assistant.handlers.append(PackageInspector())


plugin_info = {'enabled': False, 'register': register, 'command_handle': [
    'xem thư viện <tên>', 'xem tất cả thư viện',
    'xem mã <hàm|class> trong <tên thư viện>']}
