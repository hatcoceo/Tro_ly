# thêm return ở mọi nơi
import os
import shlex
from openpyxl import Workbook, load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import PatternFill
import matplotlib.pyplot as plt

def with_worksheet(func):
    """
    Decorator tự động:
    - Load workbook từ self.file (nếu chưa có thì báo lỗi)
    - Lấy active worksheet
    - Gọi func với tham số ws đầu tiên
    - Tự động save workbook sau khi func chạy (nếu không có lỗi)
    """
    def wrapper(self, *args, **kwargs):
        if not self.file:
            raise Exception("Chưa chỉ định file. Dùng -f <file> hoặc lệnh setfile")
        if not os.path.exists(self.file):
            raise Exception(f"File không tồn tại: {self.file}")
        wb = load_workbook(self.file)
        ws = wb.active
        try:
            result = func(self, ws, *args, **kwargs)
            wb.save(self.file)
            return result
        except Exception as e:
            # Không save nếu có lỗi
            raise e
    return wrapper


class ExcelProHandler:
    """
    Xử lý lệnh excel. Mọi chức năng đều là method có tên cmd_<tên_lệnh>.
    Tự động đăng ký khi khởi tạo.
    """

    def __init__(self, assistant):
        self.assistant = assistant
        self.file = None          # file mặc định
        self.commands = {}        # registry: tên lệnh -> method

        # Tự động đăng ký tất cả method bắt đầu bằng 'cmd_'
        for attr_name in dir(self):
            if attr_name.startswith('cmd_'):
                cmd_name = attr_name[4:]    # bỏ 'cmd_'
                method = getattr(self, attr_name)
                self.commands[cmd_name] = method

        # Thêm alias (có thể mở rộng)
        self.aliases = {
            'delrows': 'delete_rows_range',
            'delcolrange': 'delete_column_range',
            'avg_range': 'avg_range',
        }
        # Đăng ký alias
        for alias, target in self.aliases.items():
            if target in self.commands:
                self.commands[alias] = self.commands[target]

    def can_handle(self, command: str) -> bool:
        return command.startswith('excel')

    def handle(self, command: str):
        try:
            # Dùng shlex để parse chuỗi có dấu ngoặc kép
            parts = shlex.split(command)
            if len(parts) < 2:
                print("❌ Lệnh excel thiếu tham số")
                return None

            # Bỏ qua 'excel' ở đầu
            args = parts[1:]

            # Xử lý flag -f / --file
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
                        print("⚠️ Thiếu tên file sau -f/--file")
                        return None
                new_args.append(args[i])
                i += 1

            if filename:
                self.file = filename
            elif self.file is None:
                print("⚠️ Chưa chỉ định file. Dùng -f <tên_file> hoặc lệnh setfile")
                return None

            if not new_args:
                print("❌ Thiếu tên lệnh")
                return None

            cmd = new_args[0].lower()
            cmd_args = new_args[1:] if len(new_args) > 1 else []

            # Tìm method trong registry
            method = self.commands.get(cmd)
            if not method:
                print(f"❌ Lệnh không hợp lệ: {cmd}")
                return None

            # Gọi method và trả về kết quả
            result = method(cmd_args)
            return result

        except Exception as e:
            print(f"⚠️ Lỗi: {e}")
            return None

    # ================== ĐỊNH NGHĨA CÁC LỆNH ==================
    # Mỗi lệnh là method cmd_<tên>, với tham số args (list)
    # Nếu lệnh cần worksheet, hãy dùng decorator @with_worksheet
    # và tham số đầu tiên là ws (worksheet)

    def cmd_create(self, args):
        """Tạo file Excel mới, trả về True nếu thành công"""
        wb = Workbook()
        wb.save(self.file)
        print(f"✅ Đã tạo file {self.file}")
        return True

    @with_worksheet
    def cmd_add(self, ws, args):
        """Thêm dòng dữ liệu, trả về số dòng đã thêm (1) hoặc None nếu lỗi"""
        if not args:
            print("⚠️ excel add <giá_trị1> <giá_trị2> ...")
            return None
        row = []
        for x in args:
            try:
                row.append(float(x))
            except:
                row.append(x)
        ws.append(row)
        print(f"✅ Đã thêm: {row}")
        return row  # trả về dòng đã thêm

    @with_worksheet
    def cmd_read(self, ws, args):
        """Đọc nội dung, trả về list các dòng (mỗi dòng là tuple)"""
        data = []
        for row in ws.iter_rows(values_only=True):
            print(row)
            data.append(row)
        return data

    @with_worksheet
    def cmd_update(self, ws, args):
        """Cập nhật ô, trả về giá trị cũ hoặc None"""
        if len(args) < 3:
            print("⚠️ excel update <hàng> <cột> <giá_trị>")
            return None
        r, c = int(args[0]), int(args[1])
        val = args[2]
        # Thử chuyển đổi sang số nếu được
        try:
            val = float(val)
            if val.is_integer():
                val = int(val)
        except ValueError:
            pass  # giữ nguyên chuỗi
        old_val = ws.cell(row=r, column=c).value
        ws.cell(row=r, column=c).value = val
        print("✅ Đã cập nhật")
        return old_val


    @with_worksheet
    def cmd_delete(self, ws, args):
        """Xóa dòng, trả về số dòng đã xóa (1) hoặc None"""
        if not args:
            print("⚠️ excel delete <hàng>")
            return None
        ws.delete_rows(int(args[0]))
        print("🗑 Đã xóa dòng")
        return 1

    @with_worksheet
    def cmd_delrows(self, ws, args):
        """Xóa khoảng dòng, trả về số dòng đã xóa"""
        if len(args) < 2:
            print("⚠️ excel delrows <hàng_đầu> <hàng_cuối>")
            return None
        start, end = int(args[0]), int(args[1])
        count = end - start + 1
        ws.delete_rows(start, count)
        print(f"🗑 Đã xóa dòng {start} đến {end}")
        return count

    @with_worksheet
    def cmd_delcolrange(self, ws, args):
        """Xóa dữ liệu cột theo dòng, trả về số ô đã xóa"""
        if len(args) < 3:
            print("⚠️ excel delcolrange <cột> <hàng_đầu> <hàng_cuối>")
            return None
        col, start, end = int(args[0]), int(args[1]), int(args[2])
        count = 0
        for row in range(start, end + 1):
            ws.cell(row=row, column=col).value = None
            count += 1
        print(f"🗑 Đã xóa dữ liệu cột {col}, dòng {start}-{end}")
        return count

    @with_worksheet
    def cmd_find(self, ws, args):
        """Tìm kiếm từ khóa, trả về list các dòng chứa keyword"""
        if not args:
            print("⚠️ excel find <từ_khóa>")
            return None
        keyword = args[0]
        found_rows = []
        for row in ws.iter_rows(values_only=True):
            if any(keyword in str(cell) for cell in row):
                print("🔍", row)
                found_rows.append(row)
        if not found_rows:
            print(f"Không tìm thấy '{keyword}'")
        return found_rows

    @with_worksheet
    def cmd_avg(self, ws, args):
        """Tính trung bình tất cả số, trả về avg hoặc None"""
        nums = []
        for row in ws.iter_rows(values_only=True):
            for cell in row:
                if isinstance(cell, (int, float)):
                    nums.append(cell)
        if nums:
            avg = sum(nums) / len(nums)
            self.assistant.context['avg'] = avg
            print(f"📊 AVG = {avg}")
            return avg
        else:
            print("⚠️ Không có số nào")
            return None

    @with_worksheet
    def cmd_avg_range(self, ws, args):
        """Trung bình cột theo dòng, trả về avg hoặc None"""
        if len(args) < 3:
            print("⚠️ excel avg_range <cột> <hàng_đầu> <hàng_cuối>")
            return None
        col, start, end = int(args[0]), int(args[1]), int(args[2])
        nums = []
        for row in range(start, end + 1):
            val = ws.cell(row=row, column=col).value
            try:
                nums.append(float(val))
            except:
                continue
        if nums:
            avg = sum(nums) / len(nums)
            print(f"📊 AVG (cột {col}, dòng {start}-{end}) = {avg}")
            self.assistant.context['avg_range'] = avg
            return avg
        else:
            print("⚠️ Không có dữ liệu số trong khoảng")
            return None

    @with_worksheet
    def cmd_chart(self, ws, args):
        """Vẽ biểu đồ, trả về tên file ảnh đã lưu hoặc None"""
        data = []
        for row in ws.iter_rows(values_only=True):
            for cell in row:
                if isinstance(cell, (int, float)):
                    data.append(cell)
        if not data:
            print("⚠️ Không có dữ liệu số")
            return None
        plt.figure()
        plt.plot(data)
        plt.title("Excel Data Chart")
        plt.savefig("chart.png")
        plt.close()
        print("📈 Đã lưu chart.png")
        return "chart.png"

    @with_worksheet
    def cmd_auto(self, ws, args):
        """Quyết định BUY/WAIT dựa trên số cuối, trả về decision string"""
        data = []
        for row in ws.iter_rows(values_only=True):
            for cell in row:
                if isinstance(cell, (int, float)):
                    data.append(cell)
        if len(data) < 2:
            print("⚠️ Không đủ dữ liệu (cần ít nhất 2 số)")
            return None
        avg_prev = sum(data[:-1]) / len(data[:-1])
        last = data[-1]
        print(f"Trung bình (trừ số cuối): {avg_prev}")
        print(f"Số cuối: {last}")
        decision = "BUY" if last < avg_prev else "WAIT"
        print(f"🤖 Quyết định: {decision}")
        self.assistant.context['decision'] = decision
        return decision

    def cmd_copy(self, args):
        """Sao chép file, trả về True nếu thành công"""
        if len(args) == 1:
            source = self.file
            dest = args[0]
        elif len(args) == 2:
            source, dest = args[0], args[1]
        else:
            print("⚠️ excel copy <đích>  hoặc  excel copy <nguồn> <đích>")
            return None
        if not os.path.exists(source):
            print(f"⚠️ File nguồn không tồn tại: {source}")
            return None
        wb = load_workbook(source)
        wb.save(dest)
        print(f"✅ Đã sao chép {source} -> {dest}")
        return True

    def cmd_setfile(self, args):
        """Đặt file mặc định, trả về tên file đã đặt"""
        if not args:
            print("⚠️ excel setfile <tên_file>")
            return None
        self.file = args[0]
        print(f"📁 Đã đặt file mặc định: {self.file}")
        return self.file

    @with_worksheet
    def cmd_header(self, ws, args):
        """Sửa hàng tiêu đề, trả về số ô đã sửa"""
        if not args:
            print("⚠️ excel header <cột> \"nội dung\"  hoặc  excel header \"nd1\" \"nd2\" ...")
            return None
        if len(args) == 2 and args[0].isdigit():
            col = int(args[0])
            value = args[1].strip('"')
            ws.cell(row=1, column=col).value = value
            print(f"✅ Đã sửa tiêu đề cột {col} thành: {value}")
            return 1
        else:
            count = 0
            for idx, val in enumerate(args, start=1):
                clean_val = val.strip('"')
                ws.cell(row=1, column=idx).value = clean_val
                count += 1
            print(f"✅ Đã cập nhật {count} ô tiêu đề")
            return count

    @with_worksheet
    def cmd_comment(self, ws, args):
        """Thêm comment, trả về nội dung comment đã thêm"""
        if len(args) < 3:
            print("⚠️ excel comment <hàng> <cột> \"nội dung\"")
            return None
        row, col = int(args[0]), int(args[1])
        comment_text = ' '.join(args[2:]).strip('"')
        cell = ws.cell(row=row, column=col)
        if cell.comment:
            cell.comment = None
        cell.comment = Comment(comment_text, "User")
        print(f"✅ Đã thêm comment vào ô ({row},{col}): \"{comment_text}\"")
        return comment_text

    def cmd_manual(self, args):
        """Nhập dữ liệu thủ công, trả về số dòng đã thêm"""
        if not self.file:
            print("⚠️ Chưa chỉ định file. Dùng setfile hoặc -f trước.")
            return None
        if not os.path.exists(self.file):
            print(f"⚠️ File {self.file} chưa tồn tại, sẽ tạo mới.")
            wb = Workbook()
            wb.save(self.file)
        wb = load_workbook(self.file)
        ws = wb.active
        try:
            num_cols = int(input("Nhập số cột dữ liệu: "))
        except:
            print("❌ Số cột không hợp lệ")
            return None
        print("Nhập dữ liệu từng dòng (cách nhau bằng khoảng trắng hoặc dấu phẩy), 'done' để kết thúc")
        row_count = 0
        while True:
            line = input(f"Dòng {row_count+1}: ").strip()
            if line.lower() == 'done':
                break
            if line.lower() == 'show':
                for r in ws.iter_rows(values_only=True):
                    print(r)
                continue
            parts = line.replace(',', ' ').split()
            if len(parts) != num_cols:
                print(f"⚠️ Cần {num_cols} giá trị, bạn nhập {len(parts)}. Thử lại.")
                continue
            row_data = []
            for p in parts:
                try:
                    row_data.append(float(p))
                except:
                    row_data.append(p)
            ws.append(row_data)
            row_count += 1
            print(f"✅ Đã thêm dòng {row_count}")
        if row_count > 0:
            wb.save(self.file)
            print(f"💾 Đã lưu {row_count} dòng vào {self.file}")
        else:
            print("Không có dữ liệu nào được thêm.")
        return row_count

    @with_worksheet
    def cmd_delcol(self, ws, args):
        """Xóa hẳn một cột, trả về số cột đã xóa (1)"""
        if not args:
            print("⚠️ excel delcol <cột>")
            return None
        col = int(args[0])
        ws.delete_cols(col)
        print(f"🗑 Đã xóa cột {col}")
        return 1

    @with_worksheet
    def cmd_autofit(self, ws, args):
        """Tự động khớp độ rộng cột, trả về list các cột đã xử lý"""
        if args:
            try:
                columns = [int(a) for a in args]
            except:
                print("⚠️ Tham số cột phải là số")
                return None
        else:
            max_col = 0
            for row in ws.iter_rows(values_only=True):
                for idx, cell in enumerate(row, start=1):
                    if cell is not None and idx > max_col:
                        max_col = idx
            if max_col == 0:
                print("⚠️ Không có dữ liệu")
                return None
            columns = list(range(1, max_col + 1))

        for col in columns:
            max_length = 0
            col_letter = ws.cell(row=1, column=col).column_letter
            for row in range(1, ws.max_row + 1):
                val = ws.cell(row=row, column=col).value
                if val is not None:
                    length = len(str(val))
                    if length > max_length:
                        max_length = length
            adjusted_width = min(max(max_length + 2, 8), 50)
            ws.column_dimensions[col_letter].width = adjusted_width
        print(f"✅ Đã tự động khớp độ rộng cho {len(columns)} cột")
        return columns

    @with_worksheet
    def cmd_colorminmax(self, ws, args):
        """Tô màu min/xanh, max/hồng trong một cột, trả về tuple (min_val, max_val)"""
        if not args:
            print("⚠️ excel colorminmax <cột>")
            return None
        col = int(args[0])
        min_val = None
        max_val = None
        min_cells = []
        max_cells = []
        for row in range(2, ws.max_row + 1):
            cell = ws.cell(row=row, column=col)
            val = cell.value
            if isinstance(val, (int, float)):
                if min_val is None or val < min_val:
                    min_val = val
                    min_cells = [cell]
                elif val == min_val:
                    min_cells.append(cell)
                if max_val is None or val > max_val:
                    max_val = val
                    max_cells = [cell]
                elif val == max_val:
                    max_cells.append(cell)
        if min_val is None:
            print("⚠️ Không có dữ liệu số trong cột")
            return None
        min_fill = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")
        max_fill = PatternFill(start_color="FFC0CB", end_color="FFC0CB", fill_type="solid")
        for cell in min_cells:
            cell.fill = min_fill
        for cell in max_cells:
            cell.fill = max_fill
        print(f"✅ Đã tô màu min={min_val} (xanh) và max={max_val} (hồng) tại cột {col}")
        return (min_val, max_val)

    @with_worksheet
    def cmd_find_replace(self, ws, args):
        """Tìm và thay thế chuỗi, trả về số ô đã thay đổi"""
        if len(args) < 2:
            print("⚠️ excel find_replace \"từ_cần_tìm\" \"thay_thế\"")
            return None
        find_str = args[0].strip('"')
        replace_str = args[1].strip('"')
        count = 0
        for row in ws.iter_rows():
            for cell in row:
                if cell.value and isinstance(cell.value, str) and find_str in cell.value:
                    cell.value = cell.value.replace(find_str, replace_str)
                    count += 1
        print(f"✅ Đã thay thế '{find_str}' → '{replace_str}' trong {count} ô")
        return count

    @with_worksheet
    def cmd_remove_empty_rows(self, ws, args):
        """Xóa dòng trống, trả về số dòng đã xóa"""
        rows_to_delete = []
        for row_idx in range(1, ws.max_row + 1):
            is_empty = True
            for col_idx in range(1, ws.max_column + 1):
                if ws.cell(row=row_idx, column=col_idx).value is not None:
                    is_empty = False
                    break
            if is_empty:
                rows_to_delete.append(row_idx)
        for row_idx in reversed(rows_to_delete):
            ws.delete_rows(row_idx)
        print(f"🗑 Đã xóa {len(rows_to_delete)} dòng trống")
        return len(rows_to_delete)

    @with_worksheet
    def cmd_sort(self, ws, args):
        """Sắp xếp dữ liệu theo cột, trả về True nếu thành công"""
        if not args:
            print("⚠️ excel sort <cột> [asc|desc]")
            return None
        try:
            col = int(args[0])
        except ValueError:
            print("⚠️ Cột phải là số")
            return None
        order = args[1].lower() if len(args) > 1 else 'asc'
        reverse = (order == 'desc')
        
        data_rows = []
        for row in range(2, ws.max_row + 1):
            cell_val = ws.cell(row=row, column=col).value
            row_data = [ws.cell(row=row, column=c).value for c in range(1, ws.max_column + 1)]
            data_rows.append((cell_val, row_data))
        
        try:
            data_rows.sort(key=lambda x: x[0] if x[0] is not None else '', reverse=reverse)
        except TypeError:
            data_rows.sort(key=lambda x: str(x[0]) if x[0] is not None else '', reverse=reverse)
        
        for new_row_idx, (_, row_data) in enumerate(data_rows, start=2):
            for col_idx, val in enumerate(row_data, start=1):
                ws.cell(row=new_row_idx, column=col_idx).value = val
        print(f"✅ Đã sắp xếp theo cột {col} ({order})")
        return True

    @with_worksheet
    def cmd_stat(self, ws, args):
        """Thống kê cột, trả về dict chứa kết quả"""
        if not args:
            print("⚠️ excel stat <cột>")
            return None
        col = int(args[0])
        values = []
        null_count = 0
        for row in range(2, ws.max_row + 1):
            val = ws.cell(row=row, column=col).value
            if val is None:
                null_count += 1
            else:
                try:
                    values.append(float(val))
                except (ValueError, TypeError):
                    pass
        if not values:
            print("⚠️ Không có dữ liệu số trong cột")
            return None
        total = sum(values)
        avg_val = total / len(values)
        min_val = min(values)
        max_val = max(values)
        count = len(values)
        print(f"📊 Thống kê cột {col}:")
        print(f"   Tổng: {total}")
        print(f"   TB  : {avg_val:.2f}")
        print(f"   Min : {min_val}")
        print(f"   Max : {max_val}")
        print(f"   Số lượng số: {count}")
        print(f"   Ô trống: {null_count}")
        stats = {'sum': total, 'avg': avg_val, 'min': min_val, 'max': max_val, 'count': count, 'nulls': null_count}
        self.assistant.context[f'stat_col_{col}'] = stats
        return stats

    @with_worksheet
    def cmd_transpose(self, ws, args):
        """Chuyển vị dữ liệu, trả về tuple (số_hàng_cũ, số_cột_cũ)"""
        max_row = ws.max_row
        max_col = ws.max_column
        if max_row == 0 or max_col == 0:
            print("⚠️ Không có dữ liệu để chuyển vị")
            return None
        data = []
        for r in range(1, max_row + 1):
            row_data = []
            for c in range(1, max_col + 1):
                row_data.append(ws.cell(row=r, column=c).value)
            data.append(row_data)
        ws.delete_rows(1, ws.max_row)
        for new_c in range(1, len(data) + 1):
            for new_r in range(1, len(data[0]) + 1):
                ws.cell(row=new_r, column=new_c).value = data[new_c-1][new_r-1]
        print(f"✅ Đã chuyển vị ma trận {max_row}x{max_col} → {max_col}x{max_row}")
        return (max_row, max_col)

    @with_worksheet
    def cmd_merge_sheets(self, ws, args):
        """Hợp nhất dữ liệu từ nhiều sheet, trả về số dòng đã thêm (không kể header)"""
        if not args:
            print("⚠️ excel merge_sheets <tên_sheet1> <tên_sheet2> ...")
            return None
        wb = load_workbook(self.file)
        target_ws = wb.active
        header = None
        current_row = target_ws.max_row + 1 if target_ws.max_row > 0 else 1
        total_rows_added = 0
        
        for sheet_name in args:
            if sheet_name not in wb.sheetnames:
                print(f"⚠️ Sheet '{sheet_name}' không tồn tại, bỏ qua")
                continue
            src_ws = wb[sheet_name]
            if header is None and current_row == 1 and target_ws.max_row == 0:
                header = [src_ws.cell(row=1, column=c).value for c in range(1, src_ws.max_column + 1)]
                for col_idx, val in enumerate(header, start=1):
                    target_ws.cell(row=1, column=col_idx).value = val
                current_row = 2
                start_src_row = 2
            else:
                start_src_row = 1
            for r in range(start_src_row, src_ws.max_row + 1):
                for c in range(1, src_ws.max_column + 1):
                    val = src_ws.cell(row=r, column=c).value
                    target_ws.cell(row=current_row, column=c).value = val
                current_row += 1
                total_rows_added += 1
        wb.save(self.file)
        print(f"✅ Đã hợp nhất {len(args)} sheet vào sheet hiện tại")
        return total_rows_added

    @with_worksheet
    def cmd_formula(self, ws, args):
        """Gán công thức cho ô, trả về công thức đã gán"""
        if len(args) < 3:
            print("⚠️ excel formula <hàng> <cột> <công_thức>")
            return None
        try:
            row = int(args[0])
            col = int(args[1])
        except ValueError:
            print("⚠️ Hàng và cột phải là số")
            return None
        formula = ' '.join(args[2:]).strip()
        if not formula.startswith('='):
            formula = '=' + formula
        ws.cell(row=row, column=col).value = formula
        print(f"✅ Đã gán công thức '{formula}' vào ô ({row},{col})")
        return formula

    @with_worksheet
    def cmd_getcol(self, ws, args):
        """Lấy dữ liệu 1 cột thành list, trả về list"""
        if not args:
            print("⚠️ excel getcol <cột> [start] [end]")
            return None
        try:
            col = int(args[0])
            start = int(args[1]) if len(args) >= 2 else 1
            end = int(args[2]) if len(args) >= 3 else ws.max_row
        except ValueError:
            print("⚠️ Tham số phải là số")
            return None
        data = []
        for row in range(start, end + 1):
            val = ws.cell(row=row, column=col).value
            if val is not None:
                data.append(val)
        self.assistant.context[f'col_{col}'] = data
        return data

    @with_worksheet
    def cmd_set_range(self, ws, args):
        """
        Đặt giá trị cho một cột trong khoảng hàng.
        Cú pháp: excel set_range <cột> <hàng_đầu> <hàng_cuối> <giá_trị>
        Giá trị có thể là số hoặc chuỗi (dùng ngoặc kép nếu có dấu cách).
        Trả về số ô đã được gán giá trị.
        """
        if len(args) < 4:
            print("⚠️ excel set_range <cột> <hàng_đầu> <hàng_cuối> <giá_trị>")
            return None
        try:
            col = int(args[0])
            start_row = int(args[1])
            end_row = int(args[2])
        except ValueError:
            print("⚠️ Cột, hàng đầu, hàng cuối phải là số nguyên")
            return None
        
        # Ghép phần còn lại thành giá trị (có thể có dấu cách)
        raw_value = ' '.join(args[3:])
        # Bỏ dấu ngoặc kép nếu có
        if raw_value.startswith('"') and raw_value.endswith('"'):
            raw_value = raw_value[1:-1]
        # Thử chuyển thành số nếu được
        try:
            value = float(raw_value)
            if value.is_integer():
                value = int(value)
        except ValueError:
            value = raw_value
    
        if start_row > end_row:
            print("⚠️ Hàng đầu phải nhỏ hơn hoặc bằng hàng cuối")
            return None
    
        count = 0
        for row in range(start_row, end_row + 1):
            ws.cell(row=row, column=col).value = value
            count += 1
        print(f"✅ Đã đặt giá trị '{value}' cho cột {col}, dòng {start_row}→{end_row} (tổng {count} ô)")
        return count

    
def register(assistant):
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
        'excel -f data.xlsx header 1 "Mã số"',
        'excel -f data.xlsx header "Tên" "Tuổi" "Điểm"',
        'excel -f data.xlsx comment 2 3 "Đây là ghi chú"',
        'excel -f data.xlsx manual',
        'excel setfile myfile.xlsx',
        'excel copy backup.xlsx',
        'excel copy source.xlsx dest.xlsx',
        'excel -f data.xlsx autofit',
        'excel -f data.xlsx autofit 1 3 5',
        'excel -f data.xlsx colorminmax 2',
        'excel -f data.xlsx find_replace "old" "new"',
        'excel -f data.xlsx remove_empty_rows',
        'excel -f data.xlsx sort 2 asc',
        'excel -f data.xlsx stat 3',
        'excel -f data.xlsx transpose',
        'excel -f data.xlsx merge_sheets Sales Inventory',
        'excel -f data.xlsx formula 2 3 "=A1+B1"',
        'excel -f data.xlsx formula 4 1 "SUM(A2:A3)"',
        'excel -f data.xlsx getcol 1',
    ],
}