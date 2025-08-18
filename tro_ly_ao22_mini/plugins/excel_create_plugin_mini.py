import os
import re
plugin_info = {'name': 'Xem Dữ Liệu Excel', 'version': '1.2', 'enabled': 
    True, 'register': lambda assistant: register(assistant)}


class ExcelViewHandler:

    def __init__(self, assistant):
        self.assistant = assistant

    def can_handle(self, command: str) ->bool:
        return command.strip().lower().startswith('tạo excel')

    def handle(self, command: str):
        excel_utils = self.assistant.context.get('excel_utils')
        if not excel_utils:
            print('❌ ExcelUtils chưa được nạp!')
            return
        file_path = 'data.xlsx'
        if not os.path.exists(file_path):
            excel_utils.create_sample_workbook2(file_path)


def register(assistant):
    assistant.handlers.insert(1, ExcelViewHandler(assistant))
