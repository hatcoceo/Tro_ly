import datetime

def doc_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "Không tìm thấy file hoặc file bị lỗi."

def nhac_nho_hom_nay():
    thu = datetime.datetime.today().weekday()
    ds = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    print(f"📅 Hôm nay là {ds[thu]}.")

    if "Thứ Hai" in ds[thu]:
        print("🔔 Nhắc: Bạn thường bán được hàng vào Thứ Hai, đừng quên đăng bài!")

    noi_dung = doc_file("loi_sai.txt")
    print("\n📌 Các lỗi thường gặp của bạn:\n" + noi_dung)

def tro_chuyen():
    print("👋 Xin chào! Tôi là trợ lý ảo cá nhân của bạn.")
    nhac_nho_hom_nay()
    while True:
        cau_hoi = input("\nBạn hỏi: ")
        if cau_hoi.lower() in ['thoát', 'exit', 'quit']:
            break
        elif "lỗi" in cau_hoi:
            print("📌 Đây là các lỗi bạn đã ghi lại:\n" + doc_file("loi_sai.txt"))
        elif "nhắc" in cau_hoi:
            print("🔔 Nội dung nhắc nhở:\n" + doc_file("nhac_nho.txt"))
        else:
            print("🤖 Tôi chưa biết trả lời câu này. Bạn có thể thêm vào sau!")

tro_chuyen()
