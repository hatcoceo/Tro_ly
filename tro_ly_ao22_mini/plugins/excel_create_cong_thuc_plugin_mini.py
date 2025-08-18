from tabulate import tabulate
import os
from openpyxl import Workbook
import openpyxl
from typing import List, Dict, Any
plugin_info = {'name': 'Xem Dữ Liệu Excel', 'version': '1.2', 'enabled': 
    False, 'register': lambda assistant: register(assistant)}


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
        wb = excel_utils.load_workbook(file_path)
        sheet = excel_utils.get_sheet(wb, 'Sheet1')
        excel_utils.input_formula_from_user(sheet)
        excel_utils.save_workbook(wb, file_path)
        print(f'💾 Đã lưu file {file_path}')


def register(assistant):
    assistant.handlers.insert(1, ExcelViewHandler(assistant))
    print("📥 Plugin 'xem_du_lieu_excel' đã được đăng ký.")
