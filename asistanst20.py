from lunarcalendar import Converter, Solar
import datetime
import difflib
import os
import re
import shutil
from datetime import timedelta


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

        if cau_hoi in self.tt.tri_thuc:
            tl = "\n".join(f"- {t}" for t in self.tt.tri_thuc[cau_hoi])
            print("🧠\n" + tl)
            return True

        print("🤖 Tôi chưa biết. Bạn có thể dạy tôi bằng cú pháp: dạy: câu || trả lời")
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

    def xem_tri_thuc(self):
        if self.tt.tri_thuc:
            for cau, ds in self.tt.tri_thuc.items():
                for tl in ds:
                    print(f" - {cau} => {tl}")
        else:
            print("❌ Chưa có tri thức.")


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
