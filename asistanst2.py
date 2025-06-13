import datetime

# Đọc nội dung có chứa từ khóa trong file
def tim_noi_dung_trong_file(path, tu_khoa):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            ket_qua = []
            for dong in f:
                if tu_khoa.lower() in dong.lower():
                    ket_qua.append(dong.strip())
        return ket_qua if ket_qua else ["Không tìm thấy gì liên quan."]
    except:
        return ["Không thể mở file."]

# Xử lý câu hỏi
def tra_loi(cau_hoi):
    cau_hoi = cau_hoi.lower()

    if "quên" in cau_hoi or "lỗi" in cau_hoi:
        ket_qua = tim_noi_dung_trong_file("loi_sai.txt", "quên")
        print("📌 Một số lỗi bạn thường gặp:")
        for dong in ket_qua:
            print(" -", dong)

    elif "nhắc" in cau_hoi or "sáng" in cau_hoi or "kiểm tra" in cau_hoi:
        if "sáng" in cau_hoi:
            tu_khoa = "sáng"
        elif "kiểm tra" in cau_hoi:
            tu_khoa = "kiểm tra"
        else:
            tu_khoa = "nhắc"
        ket_qua = tim_noi_dung_trong_file("nhac_nho.txt", tu_khoa)
        print("🔔 Nhắc nhở liên quan:")
        for dong in ket_qua:
            print(" -", dong)

    elif "thứ mấy" in cau_hoi or "hôm nay" in cau_hoi:
        thu = datetime.datetime.today().weekday()
        ds = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
        print(f"📅 Hôm nay là {ds[thu]}.")

        if thu == 0:
            print("🔔 Nhắc: Hôm nay Thứ Hai – Bạn thường bán được hàng. Đừng quên đăng bài!")

    elif cau_hoi in ["thoát", "exit", "quit"]:
        return False

    else:
        print("🤖 Tôi chưa hiểu rõ. Bạn có thể hỏi lại cụ thể hơn không?")
    return True

# Bắt đầu trợ lý
def tro_chuyen():
    print("👋 Xin chào! Tôi là trợ lý ảo cá nhân của bạn.")
    while True:
        cau_hoi = input("\nBạn: ")
        if not tra_loi(cau_hoi):
            print("👋 Tạm biệt! Hẹn gặp lại.")
            break

# Gọi hàm chính
tro_chuyen()
