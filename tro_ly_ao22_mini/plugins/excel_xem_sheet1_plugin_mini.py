import os
import re
plugin_info = {'name': 'Xem Dữ Liệu Excel', 'version': '1.2', 'enabled': 
    True, 'register': lambda assistant: register(assistant)}


class ExcelViewHandler:

    def __init__(self, assistant):
        self.assistant = assistant

    def can_handle(self, command: str) ->bool:
        return command.strip().lower().startswith('xem sheet 1')

    def handle(self, command: str):
        excel_utils = self.assistant.context.get('excel_utils')
        if not excel_utils:
            print('❌ ExcelUtils chưa được nạp!')
            return
        file_path = 'data.xlsx'
        if os.path.exists(file_path):
            wb = excel_utils.load_workbook(file_path, data_only=True)
            sheet = excel_utils.get_sheet(wb, 'Sheet1')
            excel_utils.print_sheet(sheet)


def register(assistant):
    assistant.handlers.insert(1, ExcelViewHandler(assistant))
