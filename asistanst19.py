import datetime

class TriThucManager:
    def __init__(self):
        self.tri_thuc = {}

    def ghi_1_dong(self, cau, tra_loi):
        cau = cau.strip().lower()
        if cau not in self.tri_thuc:
            self.tri_thuc[cau] = []
        if tra_loi not in self.tri_thuc[cau]:
            self.tri_thuc[cau].append(tra_loi)

    def sua(self, cau, tra_loi_moi):
        cau = cau.strip().lower()
        if cau in self.tri_thuc:
            self.tri_thuc[cau] = [tra_loi_moi]
            return True
        return False

    def xoa(self, cau):
        cau = cau.strip().lower()
        if cau in self.tri_thuc:
            del self.tri_thuc[cau]
            return True
        return False

class SuKienManager:
    def __init__(self):
        self.su_kien = {}

    def ghi_su_kien(self, nd):
        today = datetime.date.today().isoformat()
        self.su_kien[nd] = today

    def xem_su_kien(self):
        if not self.su_kien:
            print("❌ Chưa có sự kiện nào.")
        else:
            for nd, ngay in self.su_kien.items():
                print(f"- {nd} (📅 {ngay})")

    def tra_loi_bao_lau(self, cau_hoi):
        for nd, ngay_str in self.su_kien.items():
            if nd in cau_hoi:
                ngay = datetime.date.fromisoformat(ngay_str)
                today = datetime.date.today()
                days = (today - ngay).days
                print(f"📅 Đã {days} ngày kể từ khi '{nd}'")
                return True
        return False

    def ghi_su_kien_nang_cao(self, cau_hoi):
        # Ví dụ: "hôm nay tao học được: ...", "vừa làm xong: ..."
        tu_khoa = ["hôm nay tao", "vừa"]
        if any(cau_hoi.startswith(tk) for tk in tu_khoa):
            self.ghi_su_kien(cau_hoi)
            print("📝 Đã ghi sự kiện nâng cao.")
            return True
        return False

class TroLyAo:
    def __init__(self):
        self.tt = TriThucManager()
        self.sk = SuKienManager()
        self.handlers = [
            self.handle_su_kien_nang_cao,
            self.handle_day,
            self.handle_xoa,
            self.handle_sua,
            self.handle_xem_tri_thuc,
            self.handle_ghi_su_kien,
            self.handle_xem_su_kien,
            self.handle_tra_loi_bao_lau,
            self.handle_tri_thuc_chinh_xac,
            self.handle_goi_y,
            self.handle_cau_dac_biet,
            self.handle_thoat,
            self.handle_chua_biet,
        ]

    def ghi_log(self, cau_hoi, tra_loi):
        today = datetime.date.today().isoformat()
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{today}] Hỏi: {cau_hoi} --> Đáp: {tra_loi}\n")

    def xu_ly_tra_loi(self, cau_hoi):
        cau_hoi = cau_hoi.strip().lower()
        for handler in self.handlers:
            if handler(cau_hoi):
                return cau_hoi not in ["thoát", "exit", "quit"]
        return True

    def handle_su_kien_nang_cao(self, cau_hoi):
        return self.sk.ghi_su_kien_nang_cao(cau_hoi)

    def handle_day(self, cau_hoi):
        if cau_hoi.startswith(("dạy:", "ghi nhớ:")):
            try:
                cau, tl = cau_hoi.split(":", 1)[1].split("||", 1)
                self.tt.ghi_1_dong(cau.strip(), tl.strip())
                print("✅ Đã ghi nhớ.")
                self.ghi_log(cau_hoi, tl)
            except:
                print("⚠️ Sai cú pháp. Dùng: dạy: câu || trả lời")
            return True
        return False

    def handle_xoa(self, cau_hoi):
        if cau_hoi.startswith("xóa:"):
            cau = cau_hoi.split(":", 1)[1].strip().lower()
            if self.tt.xoa(cau):
                print("🗑️ Đã xoá:", cau)
            else:
                print("⚠️ Không tìm thấy.")
            return True
        return False

    def handle_sua(self, cau_hoi):
        if cau_hoi.startswith("sửa:"):
            try:
                _, nd = cau_hoi.split(":", 1)
                cau, tl = nd.split("||", 1)
                if self.tt.sua(cau.strip().lower(), tl.strip()):
                    print("✏️ Đã sửa.")
                else:
                    print("⚠️ Không tìm thấy.")
            except:
                print("❗ Sai cú pháp. Dùng: sửa: câu || trả lời mới")
            return True
        return False

    def handle_xem_tri_thuc(self, cau_hoi):
        if cau_hoi == "xem tri thức":
            if self.tt.tri_thuc:
                for cau, ds in self.tt.tri_thuc.items():
                    for tl in ds:
                        print(f" - {cau} => {tl}")
            else:
                print("❌ Chưa có tri thức.")
            return True
        return False

    def handle_ghi_su_kien(self, cau_hoi):
        if cau_hoi.startswith("sự kiện:"):
            nd = cau_hoi.replace("sự kiện:", "").strip()
            if nd:
                self.sk.ghi_su_kien(nd)
                print("📝 Đã ghi sự kiện.")
            else:
                print("⚠️ Bạn chưa nhập sự kiện.")
            return True
        return False

    def handle_xem_su_kien(self, cau_hoi):
        if cau_hoi == "xem sự kiện":
            self.sk.xem_su_kien()
            return True
        return False

    def handle_tra_loi_bao_lau(self, cau_hoi):
        return self.sk.tra_loi_bao_lau(cau_hoi)

    def handle_tri_thuc_chinh_xac(self, cau_hoi):
        if cau_hoi in self.tt.tri_thuc:
            tl = "\n".join(f"- {t}" for t in self.tt.tri_thuc[cau_hoi])
            print("🧠\n" + tl)
            self.ghi_log(cau_hoi, tl)
            return True
        return False

    def handle_goi_y(self, cau_hoi):
        tu_khoa = cau_hoi.strip().lower()
        ket_qua = [cau for cau in self.tt.tri_thuc if tu_khoa in cau]
        if ket_qua:
            print("🤔 Có thể bạn muốn hỏi:")
            for cau in ket_qua[:5]:
                print(" -", cau)
            return True
        return False

    def handle_cau_dac_biet(self, cau_hoi):
        if "hôm nay là thứ mấy" in cau_hoi:
            thu = ["thứ hai", "thứ ba", "thứ tư", "thứ năm", "thứ sáu", "thứ bảy", "chủ nhật"]
            ngay = datetime.date.today().weekday()
            print("📅 Hôm nay là", thu[ngay])
            return True
        return False

    def handle_thoat(self, cau_hoi):
        return cau_hoi in ["thoát", "exit", "quit"]

    def handle_chua_biet(self, cau_hoi):
        tra_loi = input("🤖 Tôi chưa biết. Bạn trả lời giúp? ").strip()
        if tra_loi:
            self.tt.ghi_1_dong(cau_hoi, tra_loi)
            print("✅ Cảm ơn! Tôi đã học.")
            self.ghi_log(cau_hoi, tra_loi)
        else:
            self.ghi_log(cau_hoi, "Không biết")
        return True

if __name__ == "__main__":
    bot = TroLyAo()
    print("🤖 Xin chào! Tôi là trợ lý ảo. Gõ 'thoát' để kết thúc.")
    while True:
        cau_hoi = input("🧠 Hỏi tôi điều gì: ")
        if not bot.xu_ly_tra_loi(cau_hoi):
            print("👋 Tạm biệt!")
            break
