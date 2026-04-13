# thêm lệnh copy ( cả công thức )
# thêm comment
# file để sử lý yêu cầu nhập thủ công 
from openpyxl import Workbook, load_workbook
import os
import matplotlib.pyplot as plt


class ExcelProHandler:
    """
    Xử lý các lệnh thao tác với file Excel.

    Các lệnh được hỗ trợ (cú pháp: excel <flag> <lệnh> <tham số>)
    Flag: -f <tên_file> hoặc --file <tên_file> để chỉ định file thao tác.
    Nếu đã dùng lệnh setfile hoặc flag trước đó, có thể bỏ flag.

    Các lệnh:
        - excel -f ten.xlsx create                      : Tạo file ten.xlsx mới
        - excel -f ten.xlsx add giá_trị1 giá_trị2 ...   : Thêm dòng dữ liệu
        - excel -f ten.xlsx read                        : Đọc nội dung
        - excel -f ten.xlsx update hàng cột giá_trị     : Cập nhật ô
        - excel -f ten.xlsx delete hàng                 : Xóa dòng
        - excel -f ten.xlsx delrows hàng_đầu hàng_cuối  : Xóa khoảng dòng
        - excel -f ten.xlsx delcolrange cột hàng_đầu hàng_cuối : Xóa dữ liệu cột theo dòng
        - excel -f ten.xlsx find từ_khóa                : Tìm kiếm
        - excel -f ten.xlsx avg                         : Tính trung bình toàn bộ số
        - excel -f ten.xlsx avg_range cột hàng_đầu hàng_cuối : Trung bình cột theo dòng
        - excel -f ten.xlsx chart                       : Vẽ biểu đồ
        - excel -f ten.xlsx auto                        : Quyết định BUY/WAIT
        - excel setfile ten.xlsx                        : Thiết lập file mặc định
        - excel copy [nguồn] đích                       : Sao chép file (giữ công thức)

    Kết quả tính toán (avg, decision, avg_range) được lưu vào assistant.context.
    """

    def __init__(self, assistant):
        """
        Khởi tạo bộ xử lý Excel.

        Args:
            assistant: Đối tượng assistant chính, dùng để chia sẻ context.
        """
        self.file = None  # Không hardcode, sẽ được set qua flag hoặc lệnh setfile
        self.assistant = assistant
        self.action_map = {
            'create': self.create,
            'add': self.add,
            'read': self.read,
            'update': self.update,
            'delete': self.delete,
            'delrows': self.delete_rows_range,
            'delcolrange': self.delete_column_range,
            'find': self.find,
            'avg': self.avg,
            'chart': self.chart,
            'auto': self.auto_decision,
            'avg_range': self.avg_range,
            'copy': self.copy,
            'setfile': self.setfile,
        }

    def can_handle(self, command: str) -> bool:
        return command.startswith('excel')

    def handle(self, command: str):
        """
        Xử lý lệnh excel: phân tích flag, lấy tên file, gọi phương thức tương ứng.
        """
        try:
            parts = command.split()
            if len(parts) < 2:
                print('❌ Lệnh không hợp lệ')
                return

            # Loại bỏ phần tử 'excel' đầu tiên
            args = parts[1:]

            # Tìm flag -f/--file
            new_args = []
            filename = None
            i = 0
            while i < len(args):
                if args[i] in ('-f', '--file'):
                    if i + 1 < len(args):
                        filename = args[i + 1]
                        i += 2
                        continue
                    else:
                        print('⚠️ Thiếu tên file sau -f/--file')
                        return
                new_args.append(args[i])
                i += 1

            # Cập nhật file hiện tại nếu có flag
            if filename:
                self.file = filename
            elif self.file is None:
                # Chưa có file nào được set
                print('⚠️ Chưa chỉ định file. Vui lòng dùng -f <tên_file> hoặc lệnh setfile')
                return

            if not new_args:
                print('❌ Lệnh không hợp lệ')
                return

            action = new_args[0]
            method = self.action_map.get(action)
            if method:
                # Truyền các tham số còn lại (không có 'excel', không có flag)
                method(new_args[1:] if len(new_args) > 1 else [])
            else:
                print('❌ Lệnh không hợp lệ')
        except Exception as e:
            print(f'⚠️ Lỗi: {e}')

    # ------------------- Các phương thức thao tác với Excel -------------------

    def create(self, args=None):
        """Tạo file Excel mới (args không dùng)."""
        wb = Workbook()
        wb.save(self.file)
        print(f'✅ Đã tạo file {self.file}')

    def add(self, args):
        """
        Thêm dòng dữ liệu.
        args: list các giá trị (chuỗi hoặc số)
        """
        if not args:
            print('⚠️ excel add <giá_trị1> <giá_trị2> ...')
            return
        wb = self._load()
        if not wb:
            return
        ws = wb.active
        row = []
        for x in args:
            try:
                row.append(float(x))
            except:
                row.append(x)
        ws.append(row)
        wb.save(self.file)
        print(f'✅ Đã thêm: {row}')

    def read(self, args=None):
        """Đọc và in toàn bộ nội dung sheet."""
        wb = self._load()
        if not wb:
            return
        ws = wb.active
        for r in ws.iter_rows(values_only=True):
            print(r)

    def update(self, args):
        """
        Cập nhật ô.
        args: [hàng, cột, giá_trị]
        """
        if len(args) < 3:
            print('⚠️ excel update <hàng> <cột> <giá_trị>')
            return
        wb = self._load()
        if not wb:
            return
        ws = wb.active
        r, c = int(args[0]), int(args[1])
        val = args[2]
        ws.cell(row=r, column=c).value = val
        wb.save(self.file)
        print('✅ Đã cập nhật')

    def delete(self, args):
        """
        Xóa một dòng.
        args: [hàng]
        """
        if not args:
            print('⚠️ excel delete <hàng>')
            return
        wb = self._load()
        if not wb:
            return
        ws = wb.active
        ws.delete_rows(int(args[0]))
        wb.save(self.file)
        print('🗑 Đã xóa dòng')

    def find(self, args):
        """
        Tìm từ khóa.
        args: [từ_khóa]
        """
        if not args:
            print('⚠️ excel find <từ_khóa>')
            return
        keyword = args[0]
        wb = self._load()
        if not wb:
            return
        ws = wb.active
        found = False
        for row in ws.iter_rows(values_only=True):
            if any(keyword in str(cell) for cell in row):
                print('🔍', row)
                found = True
        if not found:
            print(f'Không tìm thấy "{keyword}"')

    def avg(self, args=None):
        """Tính trung bình tất cả số trong file."""
        wb = self._load()
        if not wb:
            return
        ws = wb.active
        nums = []
        for row in ws.iter_rows(values_only=True):
            for cell in row:
                if isinstance(cell, (int, float)):
                    nums.append(cell)
        if nums:
            avg = sum(nums) / len(nums)
            self.assistant.context['avg'] = avg
            print(f'📊 AVG = {avg}')
        else:
            print('⚠️ Không có số nào')

    def chart(self, args=None):
        """Vẽ biểu đồ đường và lưu chart.png."""
        wb = self._load()
        if not wb:
            return
        ws = wb.active
        data = []
        for row in ws.iter_rows(values_only=True):
            for cell in row:
                if isinstance(cell, (int, float)):
                    data.append(cell)
        if not data:
            print('⚠️ Không có dữ liệu số')
            return
        plt.figure()
        plt.plot(data)
        plt.title('Excel Data Chart')
        plt.savefig('chart.png')
        plt.close()
        print('📈 Đã lưu chart.png')

    def auto_decision(self, args=None):
        """Đưa ra quyết định BUY/WAIT dựa trên số cuối so với trung bình các số trước."""
        wb = self._load()
        if not wb:
            return
        ws = wb.active
        data = []
        for row in ws.iter_rows(values_only=True):
            for cell in row:
                if isinstance(cell, (int, float)):
                    data.append(cell)
        if len(data) < 2:
            print('⚠️ Không đủ dữ liệu (cần ít nhất 2 số)')
            return
        avg_prev = sum(data[:-1]) / len(data[:-1])
        last = data[-1]
        print(f'Trung bình (trừ số cuối): {avg_prev}')
        print(f'Số cuối: {last}')
        decision = 'BUY' if last < avg_prev else 'WAIT'
        print(f'🤖 Quyết định: {decision}')
        self.assistant.context['decision'] = decision

    def _load(self):
        """Tải workbook từ self.file."""
        if not self.file:
            print('⚠️ Chưa có file nào được chỉ định')
            return None
        if not os.path.exists(self.file):
            print(f'⚠️ File không tồn tại: {self.file}')
            return None
        return load_workbook(self.file)

    def avg_range(self, args):
        """
        Tính trung bình các số trong một cột trên khoảng dòng.
        args: [cột, hàng_đầu, hàng_cuối]
        """
        if len(args) < 3:
            print('⚠️ excel avg_range <cột> <hàng_đầu> <hàng_cuối>')
            return
        wb = self._load()
        if not wb:
            return
        ws = wb.active
        col = int(args[0])
        start = int(args[1])
        end = int(args[2])
        nums = []
        for r in range(start, end + 1):
            val = ws.cell(row=r, column=col).value
            try:
                nums.append(float(val))
            except:
                continue
        if nums:
            avg = sum(nums) / len(nums)
            print(f'📊 AVG (cột {col}, dòng {start}-{end}) = {avg}')
            self.assistant.context['avg_range'] = avg
        else:
            print('⚠️ Không có dữ liệu số trong khoảng')

    def delete_rows_range(self, args):
        """
        Xóa khoảng dòng.
        args: [hàng_đầu, hàng_cuối]
        """
        if len(args) < 2:
            print('⚠️ excel delrows <hàng_đầu> <hàng_cuối>')
            return
        wb = self._load()
        if not wb:
            return
        ws = wb.active
        start = int(args[0])
        end = int(args[1])
        count = end - start + 1
        ws.delete_rows(start, count)
        wb.save(self.file)
        print(f'🗑 Đã xóa dòng {start} đến {end}')

    def delete_column_range(self, args):
        """
        Xóa dữ liệu trong một cột trên khoảng dòng.
        args: [cột, hàng_đầu, hàng_cuối]
        """
        if len(args) < 3:
            print('⚠️ excel delcolrange <cột> <hàng_đầu> <hàng_cuối>')
            return
        wb = self._load()
        if not wb:
            return
        ws = wb.active
        col = int(args[0])
        start = int(args[1])
        end = int(args[2])
        for row in range(start, end + 1):
            ws.cell(row=row, column=col).value = None
        wb.save(self.file)
        print(f'🗑 Đã xóa dữ liệu cột {col}, dòng {start} đến {end}')

    def copy(self, args):
        """
        Sao chép file Excel (giữ công thức).
        args: [đích] hoặc [nguồn, đích]
        """
        if len(args) == 1:
            source = self.file
            dest = args[0]
        elif len(args) == 2:
            source = args[0]
            dest = args[1]
        else:
            print('⚠️ excel copy <đích>  hoặc  excel copy <nguồn> <đích>')
            return

        if not os.path.exists(source):
            print(f'⚠️ File nguồn không tồn tại: {source}')
            return

        try:
            wb = load_workbook(source)
            wb.save(dest)
            print(f'✅ Đã sao chép {source} -> {dest} (giữ nguyên công thức)')
        except Exception as e:
            print(f'❌ Lỗi sao chép: {e}')

    def setfile(self, args):
        """
        Thiết lập file mặc định cho các lệnh tiếp theo.
        args: [tên_file]
        """
        if not args:
            print('⚠️ excel setfile <tên_file>')
            return
        self.file = args[0]
        print(f'📁 Đã đặt file mặc định: {self.file}')


def register(assistant):
    """Đăng ký handler vào assistant."""
    assistant.handlers.append(ExcelProHandler(assistant))


plugin_info = {
    'enabled': True,
    'register': register,
    'command_handle': [
        'excel -f data.xlsx create',
        'excel -f data.xlsx add 10 20 30',
        'excel -f data.xlsx read',
        'excel -f data.xlsx update 2 1 hello',
        'excel -f data.xlsx delete 2',
        'excel -f data.xlsx delrows 1 10',
        'excel -f data.xlsx delcolrange 1 2 5',
        'excel -f data.xlsx find 20',
        'excel -f data.xlsx avg',
        'excel -f data.xlsx avg_range 1 2 4',
        'excel -f data.xlsx chart',
        'excel -f data.xlsx auto',
        'excel setfile myfile.xlsx',
        'excel copy backup.xlsx',
        'excel copy source.xlsx dest.xlsx',
    ],
}