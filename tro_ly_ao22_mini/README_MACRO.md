macro.py
├── Cấu hình toàn cục
│   └── macro_folder, recorder_is_playing
│
├── Exceptions
│   ├── BreakException
│   ├── ContinueException
│   └── AssertionFailedError
│
├── MacroRecorder          # Ghi lại lệnh vào file
│
├── Lớp tiện ích (DRY)
│   ├── StringUtils        # Xử lý chuỗi (strip quotes)
│   ├── VariableResolver   # Nội suy biến {var}, tính toán biểu thức
│   ├── ConditionEvaluator # Đánh giá điều kiện (AND/OR/NOT/so sánh)
│   └── AutoInputHelper    # Hàng đợi input tự động
│
├── MacroContext           # Trạng thái runtime (biến, hàm, delay...)
│
├── MacroCommand (ABC)     # Base class cho mọi lệnh
│   └── [30+ Command classes]
│
├── CommandRegistry        # Đăng ký và dispatch parser (Open/Closed Principle)
│
├── MacroParser            # Phân tích cú pháp file macro → AST lệnh
│
├── MacroExecutor          # Thực thi cây lệnh
│
├── MacroCommandHandler    # Xử lý lệnh ghi/chạy macro từ người dùng
│
└── plugin_info            # Metadata tích hợp plugin

Biến
SET ten = "Alice"
SET so = 10 + 5
PRINT Xin chào {ten}!
DEL ten

Điều kiện
IF {so} > 10
    PRINT Lớn hơn 10
ELIF {so} == 10
    PRINT Bằng 10
ELSE
    PRINT Nhỏ hơn 10
ENDIF

Vòng lặp
# Lặp n lần
LOOP 5
    PRINT Lần lặp
ENDLOOP

# Lặp qua danh sách
FOREACH item IN táo, cam, chuối
    PRINT {item}
ENDFOREACH

# Lặp với điều kiện
SET dem = 0
WHILE {dem} < 3
    SET dem = {dem} + 1
    PRINT Đếm: {dem}
ENDWHILE

BREAK và CONTINUE
LOOP 10
    IF {i} == 3
        BREAK
    ENDIF
    IF {i} == 1
        CONTINUE
    ENDIF
ENDLOOP

Hàm
FUNCTION chao(ten)
    PRINT Xin chào {ten}!
    RETURN {ten}
ENDFUNCTION
CALL chao("Alice") -> ket_qua
PRINT Kết quả: {ket_qua}

Input và Câu hỏi
# Đẩy giá trị vào hàng đợi input
INPUT Alice

# Hỏi người dùng (lưu vào {answer})
? Bạn tên gì?

# Câu hỏi với trả lời tự động
? Bạn tên gì? auto: Bob

Import
# Import toàn bộ macro khác
IMPORT ten_macro_khac

# Import chỉ một số hàm
FROM thu_vien IMPORT ham1, ham2

Nhúng Python
# Một biểu thức/lệnh Python
PYTHON len("hello") -> do_dai
PRINT Độ dài: {do_dai}

# Khối Python nhiều dòng
PYBLOCK -> ket_qua
    x = 10
    y = 20
    result = x + y
ENDPYBLOCK
PRINT {ket_qua}

Xử lý ngoại lệ
TRY
    PYTHON 1 / 0
EXCEPT ZeroDivisionError AS loi
    PRINT Lỗi chia cho 0: {loi}
FINALLY
    PRINT Luôn chạy cuối
ENDTRY

Pattern Matching
SET ngay = "Thu2"
MATCH {ngay}
    CASE Thu2
        PRINT Đầu tuần
    CASE Thu6
        PRINT Cuối tuần
    DEFAULT
        PRINT Ngày thường
ENDMATCH

Context Manager (WITH)
WITH open("file.txt", "r") AS f
    PYTHON f.read() -> noi_dung
    PRINT {noi_dung}
ENDWITH

ASSERT
SET gia_tri = 42
ASSERT {gia_tri} > 0, Giá trị phải dương

RAISE
RAISE ValueError("Dữ liệu không hợp lệ")

SILENT – Thực thi không in log
SILENT ten_lenh_nao_do
SILENT ten_lenh -> bien_luu

Lưu kết quả lệnh vào biến
ten_lenh_bat_ky -> bien_ket_qua
PRINT {bien_ket_qua}

Lệnh điều khiển Macro (từ giao diện người dùng)
ghi macro <tên>       # Bắt đầu ghi macro
dừng ghi macro        # Dừng ghi và lưu file
chạy macro <tên>      # Chạy macro (delay mặc định 1.0s)
chạy macro <tên> 0.5  # Chạy với delay tùy chỉnh (giây)

File: macros/vi_du.txt
SET ten = "Macro Engine"
SET phien_ban = 2

PRINT Chào mừng đến với {ten} v{phien_ban}!

FUNCTION tinh_tong(a, b)
    SET tong = {a} + {b}
    RETURN {tong}
ENDFUNCTION

CALL tinh_tong(10, 25) -> ket_qua
PRINT Tổng: {ket_qua}

IF {ket_qua} > 30
    PRINT Kết quả lớn hơn 30
ELSE
    PRINT Kết quả không lớn hơn 30
ENDIF

FOREACH mon IN Toán, Lý, Hóa
    PRINT Môn học: {mon}
ENDFOREACH

TRY
    ASSERT {ket_qua} > 100, Kết quả quá nhỏ
EXCEPT AssertionFailedError AS loi
    PRINT Bắt lỗi: {loi}
ENDTRY

PRINT Hoàn thành!
