import pkg_resources


class PackageLister:

    def can_handle(self, command: str) ->bool:
        return command in ['danh sách thư viện', 'liệt kê thư viện',
            'list packages']

    def handle(self, command: str) ->None:
        print('📦 Các thư viện đã cài đặt:')
        try:
            packages = sorted(['{}=={}'.format(d.project_name, d.version) for
                d in pkg_resources.working_set])
            for idx, pkg in enumerate(packages, start=1):
                print(f'{idx:3}. {pkg}')
        except Exception as e:
            print(f'⚠️ Không thể lấy danh sách thư viện: {e}')


def register(assistant):
    assistant.handlers.append(PackageLister())


plugin_info = {'enabled': False, 'register': register, 'command_handle': [
    'danh sách thư viện', 'liệt kê thư viện', 'list packages']}
