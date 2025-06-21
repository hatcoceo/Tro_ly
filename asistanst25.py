# tim kiem.
# chua co { tao van ban}
from lunarcalendar import Converter, Solar
import datetime
import difflib
import os
import re
import shutil
from datetime import timedelta
import math


class FileManager:
    @staticmethod
    def them_vao_file(file_path, noi_dung):
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(noi_dung + "\n")

    @staticmethod
    def doc_file(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return [dong.strip() for dong in f if dong.strip()]
        except:
            return []

    @staticmethod
    def ghi_de_file(file_path, danh_sach_dong):
        with open(file_path, "w", encoding="utf-8") as f:
            for dong in danh_sach_dong:
                f.write(dong + "\n")


class TriThucManager:
    def __init__(self, path="tri_thuc.txt"):
        self.path = path
        self.tri_thuc = self.doc_tri_thuc()

    def doc_tri_thuc(self):
        tri_thuc = {}
        for dong in FileManager.doc_file(self.path):
            if "||" in dong:
                cau, tl = dong.split("||", 1)
                tri_thuc.setdefault(cau.strip().lower(), []).append(tl.strip())
        return tri_thuc

    def ghi_lai_tri_thuc(self):
        if os.path.exists(self.path):
            shutil.copy(self.path, "tri_thuc_backup.txt")
        ds_dong = [f"{cau}||{tl}" for cau, ds in self.tri_thuc.items() for tl in ds]
        FileManager.ghi_de_file(self.path, ds_dong)

    def ghi_1_dong(self, cau, tl):
        FileManager.them_vao_file(self.path, f"{cau.strip().lower()}||{tl.strip()}")
        self.tri_thuc.setdefault(cau.strip().lower(), []).append(tl.strip())

    def xoa(self, cau):
        if cau in self.tri_thuc:
            del self.tri_thuc[cau]
            self.ghi_lai_tri_thuc()
            return True
        return False

    def sua(self, cau, tra_loi_moi):
        if cau in self.tri_thuc:
            self.tri_thuc[cau] = [tra_loi_moi.strip()]
            self.ghi_lai_tri_thuc()
            return True
        return False

    def tim_kiem(self, tu_khoa):
        tu_khoa = tu_khoa.lower()
        ket_qua = []
        for cau, ds in self.tri_thuc.items():
            if tu_khoa in cau:
                for tl in ds:
                    ket_qua.append((cau, tl))
        return ket_qua


class SuKienManager:
    def __init__(self, path="su_kien.txt"):
        self.path = path

    def ghi_su_kien(self, su_kien):
        tg = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        FileManager.them_vao_file(self.path, f"{tg} || {su_kien}")

    def xem_su_kien(self):
        ds = FileManager.doc_file(self.path)
        if not ds:
            print("📭 Không có sự kiện nào.")
        else:
            print("📅 Danh sách sự kiện:")
            for dong in ds:
                print(" -", dong)

    def tinh_so_ngay_da_qua(self, thoi_gian_str):
        try:
            goc = datetime.datetime.strptime(thoi_gian_str, "%Y-%m-%d %H:%M:%S")
            return (datetime.datetime.now() - goc).days
        except:
            return None

    def tra_loi_bao_lau(self, cau_hoi):
        tim = cau_hoi.replace("diễn ra bao lâu", "").replace("bao lâu rồi", "").strip(" ?")
        danh_sach = FileManager.doc_file(self.path)
        ket_qua = []

        for dong in danh_sach:
            if "||" in dong:
                tg, nd = dong.split("||", 1)
                if tim.lower() in nd.strip().lower():
                    so_ngay = self.tinh_so_ngay_da_qua(tg.strip())
                    if so_ngay is not None:
                        ket_qua.append((nd.strip(), so_ngay, tg.strip()))

        if ket_qua:
            for nd, so_ngay, tg in ket_qua:
                print(f"📆 Sự kiện '{nd}' diễn ra vào {tg}, cách đây {so_ngay} ngày.")
            return True
        else:
            print("🔎 Không tìm thấy sự kiện.")
            return True

    def ghi_su_kien_nang_cao(self, cau_hoi):
        match = re.search(r"(\d+)\s*ngày\s*rồi", cau_hoi.lower())
        if match:
            so_ngay = int(match.group(1))
            ngay_bat_dau = datetime.datetime.now() - timedelta(days=so_ngay)
            ngay_bat_dau_str = ngay_bat_dau.strftime("%Y-%m-%d %H:%M:%S")
            noi_dung = re.sub(r"đã|(\d+\s*ngày\s*rồi)", "", cau_hoi, flags=re.I).strip()
            if not noi_dung:
                noi_dung = "Sự kiện"
            su_kien_ghi = f"{noi_dung} - bắt đầu từ {ngay_bat_dau_str}"
            self.ghi_su_kien(su_kien_ghi)
            print(f"📝 Đã ghi sự kiện nâng cao: '{su_kien_ghi}'")
            return True
        return False


class CommandHandler:
    def __init__(self, tt, sk):
        self.tt = tt
        self.sk = sk
        self.prefix_handlers = {
            "dạy:": self.xu_ly_day,
            "ghi nhớ:": self.xu_ly_day,
            "xóa:": self.xu_ly_xoa,
            "sửa:": self.xu_ly_sua,
            "sự kiện:": self.xu_ly_ghi_su_kien,
            "tìm:": self.xu_ly_tim_kiem,
        }
        self.special_cases = {
            "xem tri thức": self.xem_tri_thuc,
            "xem sự kiện": self.sk.xem_su_kien,
            "thoát": lambda: False,
            "exit": lambda: False,
            "quit": lambda: False,
        }

    def xu_ly_tra_loi(self, cau_hoi):
        cau_hoi = cau_hoi.strip().lower()

        if self.sk.ghi_su_kien_nang_cao(cau_hoi):
            return True

        for prefix, handler in self.prefix_handlers.items():
            if cau_hoi.startswith(prefix):
                handler(cau_hoi)
                return True

        if cau_hoi in self.special_cases:
            result = self.special_cases[cau_hoi]()
            return result if result is not None else True

        if "bao lâu" in cau_hoi:
            return self.sk.tra_loi_bao_lau(cau_hoi)

        # 🧮 Tính toán nếu là biểu thức toán học
        if re.match(r"^[\d\s\+\-\*/\.\%\(\)]+$", cau_hoi):
            return self.tinh_toan_bieu_thuc(cau_hoi)

        # ✅ Trả lời lịch âm và dương hôm nay
        if cau_hoi in ["hôm nay là thứ mấy", "hôm nay là ngày gì", "nay thứ mấy", "hôm nay ngày bao nhiêu"]:
            ngay_hom_nay = datetime.datetime.now()
            thu = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"][ngay_hom_nay.weekday()]
            ngay_duong = ngay_hom_nay.strftime("%d/%m/%Y")

            solar = Solar(ngay_hom_nay.year, ngay_hom_nay.month, ngay_hom_nay.day)
            lunar = Converter.Solar2Lunar(solar)
            ngay_am = f"{lunar.day}/{lunar.month}/{lunar.year}"

            print(f"📅 Hôm nay là {thu}, ngày {ngay_duong} (Dương lịch)")
            print(f"🌙 Lịch âm: {ngay_am}")
            return True

        if cau_hoi in self.tt.tri_thuc:
            tl = "\n".join(f"- {t}" for t in self.tt.tri_thuc[cau_hoi])
            print("🧠\n" + tl)
            return True

        if self.goi_y_cau_hoi(cau_hoi):
            return True
        self.xu_ly_hoc_them(cau_hoi)
        return True

    def tinh_toan_bieu_thuc(self, bieu_thuc):
        try:
            allowed_chars = "0123456789+-*/().% "
            if all(c in allowed_chars for c in bieu_thuc):
                ket_qua = eval(bieu_thuc)
                print(f"🧮 Kết quả: {ket_qua}")
                return True
            else:
                print("⚠️ Biểu thức chứa ký tự không hợp lệ.")
                return True
        except:
            print("❌ Không thể tính được. Biểu thức sai cú pháp.")
            return True

    def xu_ly_day(self, cau_hoi):
        try:
            _, nd = cau_hoi.split(":", 1)
            cau, tl = nd.split("||", 1)
            self.tt.ghi_1_dong(cau, tl)
            print("✅ Đã ghi thêm.")
        except:
            print("❗ Sai cú pháp. Dùng: dạy: câu || trả lời")

    def xu_ly_xoa(self, cau_hoi):
        cau = cau_hoi.split(":", 1)[1].strip().lower()
        if self.tt.xoa(cau):
            print("🗑️ Đã xoá:", cau)
        else:
            print("⚠️ Không tìm thấy.")

    def xu_ly_sua(self, cau_hoi):
        try:
            _, nd = cau_hoi.split(":", 1)
            cau, tl = nd.split("||", 1)
            if self.tt.sua(cau.strip().lower(), tl.strip()):
                print("✏️ Đã sửa.")
            else:
                print("⚠️ Không tìm thấy.")
        except:
            print("❗ Sai cú pháp. Dùng: sửa: câu || trả lời mới")

    def xu_ly_ghi_su_kien(self, cau_hoi):
        nd = cau_hoi.split(":", 1)[1].strip()
        if nd:
            self.sk.ghi_su_kien(nd)
            print("📝 Đã ghi sự kiện.")
        else:
            print("⚠️ Bạn chưa nhập sự kiện.")

    def xu_ly_tim_kiem(self, cau_hoi):
        tu_khoa = cau_hoi.split(":", 1)[1].strip().lower()
        ket_qua = self.tt.tim_kiem(tu_khoa)
        if ket_qua:
            print(f"🔍 Tìm thấy {len(ket_qua)} kết quả:")
            for cau, tl in ket_qua:
                print(f" - {cau} => {tl}")
        else:
            print("❌ Không tìm thấy tri thức nào chứa từ khoá đó.")

    def xem_tri_thuc(self):
        if self.tt.tri_thuc:
            for cau, ds in self.tt.tri_thuc.items():
                for tl in ds:
                    print(f" - {cau} => {tl}")
        else:
            print("❌ Chưa có tri thức.")

    def goi_y_cau_hoi(self, cau_hoi, so_luong=5):
        danh_sach_cau = list(self.tt.tri_thuc.keys())
        gan_giong = difflib.get_close_matches(cau_hoi, danh_sach_cau, n=so_luong, cutoff=0.6)
        if gan_giong:
            print("❓ Bạn có định hỏi một trong những câu sau không:")
            for i, cau in enumerate(gan_giong, 1):
                print(f" {i}. {cau}")
            lua_chon = input("👉 Nhập số để chọn hoặc Enter để bỏ qua: ").strip()
            if lua_chon.isdigit():
                chon = int(lua_chon)
                if 1 <= chon <= len(gan_giong):
                    cau_chon = gan_giong[chon - 1]
                    tl = "\n".join(f"- {t}" for t in self.tt.tri_thuc[cau_chon])
                    print("🧠\n" + tl)
                    return True
        return False

    def xu_ly_hoc_them(self, cau_hoi):
        tra_loi_nguoi_dung = input("🤖 Tôi chưa biết. Bạn có thể trả lời giúp tôi không? (nếu có, gõ câu trả lời): ").strip()
        if tra_loi_nguoi_dung:
            self.tt.ghi_1_dong(cau_hoi, tra_loi_nguoi_dung)
            print("✅ Cảm ơn! Tôi đã học thêm.")
        else:
            print("🤖 Tôi sẽ tìm hiểu thêm về điều này.")


class TroLyAo:
    def __init__(self):
        self.tt = TriThucManager()
        self.sk = SuKienManager()
        self.handler = CommandHandler(self.tt, self.sk)

    def bat_dau(self):
        print("👋 Xin chào! Tôi là trợ lý ảo.")
        while True:
            cau_hoi = input("\nBạn: ")
            ket_qua = self.handler.xu_ly_tra_loi(cau_hoi)
            if ket_qua is False:
                print("👋 Tạm biệt!")
                break


if __name__ == "__main__":
    TroLyAo().bat_dau()
