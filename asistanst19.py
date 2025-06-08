import datetime

tri_thuc = {}
su_kien = {}

def ghi_1_dong(cau, tra_loi):
    cau = cau.strip().lower()
    if cau not in tri_thuc:
        tri_thuc[cau] = []
    if tra_loi not in tri_thuc[cau]:
        tri_thuc[cau].append(tra_loi)

def sua(cau, tra_loi_moi):
    cau = cau.strip().lower()
    if cau in tri_thuc:
        tri_thuc[cau] = [tra_loi_moi]
        return True
    return False

def xoa(cau):
    cau = cau.strip().lower()
    if cau in tri_thuc:
        del tri_thuc[cau]
        return True
    return False

def ghi_su_kien(nd):
    su_kien[nd] = datetime.date.today().isoformat()

def xem_su_kien():
    if not su_kien:
        print("❌ Chưa có sự kiện nào.")
    else:
        for nd, ngay in su_kien.items():
            print(f"- {nd} (📅 {ngay})")

def tra_loi_bao_lau(cau_hoi):
    for nd, ngay_str in su_kien.items():
        if nd in cau_hoi:
            ngay = datetime.date.fromisoformat(ngay_str)
            hom_nay = datetime.date.today()
            print(f"📅 Đã {(hom_nay - ngay).days} ngày kể từ '{nd}'")
            return True
    return False

def ghi_log(cau_hoi, tra_loi):
    today = datetime.date.today().isoformat()
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{today}] Hỏi: {cau_hoi} --> Đáp: {tra_loi}\n")

def xu_ly(cau_hoi):
    ch = cau_hoi.strip().lower()

    # Ghi sự kiện nâng cao
    if ch.startswith("hôm nay tao") or ch.startswith("vừa "):
        ghi_su_kien(ch)
        print("📝 Đã ghi sự kiện nâng cao.")
        return

    if ch.startswith("dạy:") or ch.startswith("ghi nhớ:"):
        try:
            cau, tl = ch.split(":", 1)[1].split("||", 1)
            ghi_1_dong(cau.strip(), tl.strip())
            print("✅ Đã ghi nhớ.")
            ghi_log(cau_hoi, tl)
        except:
            print("⚠️ Dùng: dạy: câu || trả lời")
        return

    if ch.startswith("sửa:"):
        try:
            cau, tl = ch.split(":", 1)[1].split("||", 1)
            if sua(cau.strip(), tl.strip()):
                print("✏️ Đã sửa.")
            else:
                print("❌ Không tìm thấy.")
        except:
            print("❗ Dùng: sửa: câu || trả lời")
        return

    if ch.startswith("xóa:"):
        cau = ch.split(":", 1)[1].strip()
        if xoa(cau):
            print("🗑️ Đã xoá.")
        else:
            print("❌ Không tìm thấy.")
        return

    if ch == "xem tri thức":
        if tri_thuc:
            for cau, ds in tri_thuc.items():
                for tl in ds:
                    print(f"- {cau} => {tl}")
        else:
            print("❌ Chưa có tri thức.")
        return

    if ch == "xem sự kiện":
        xem_su_kien()
        return

    if ch.startswith("sự kiện:"):
        nd = ch.replace("sự kiện:", "").strip()
        if nd:
            ghi_su_kien(nd)
            print("📝 Đã ghi sự kiện.")
        else:
            print("⚠️ Chưa nhập nội dung.")
        return

    if tra_loi_bao_lau(ch):
        return

    if "hôm nay là thứ mấy" in ch:
        thu = ["thứ hai", "thứ ba", "thứ tư", "thứ năm", "thứ sáu", "thứ bảy", "chủ nhật"]
        print("📅 Hôm nay là", thu[datetime.date.today().weekday()])
        return

    if ch in tri_thuc:
        for tl in tri_thuc[ch]:
            print("🧠", tl)
            ghi_log(cau_hoi, tl)
        return

    goi_y = [c for c in tri_thuc if ch in c]
    if goi_y:
        print("🤔 Có thể bạn muốn hỏi:")
        for g in goi_y[:5]:
            print(" -", g)
        return

    tl = input("🤖 Tôi chưa biết. Bạn trả lời giúp? ").strip()
    if tl:
        ghi_1_dong(ch, tl)
        print("✅ Cảm ơn! Tôi đã học.")
        ghi_log(cau_hoi, tl)
    else:
        ghi_log(cau_hoi, "Không biết")

if __name__ == "__main__":
    print("🤖 Xin chào! Gõ 'thoát' để kết thúc.")
    while True:
        ch = input("🧠 Hỏi: ").strip()
        if ch.lower() in ["thoát", "exit", "quit"]:
            print("👋 Tạm biệt!")
            break
        xu_ly(ch)
