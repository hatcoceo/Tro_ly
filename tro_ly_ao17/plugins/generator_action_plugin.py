# sử lý : tạo hành động cho tu_chen
from typing import List
from random import choice

# Khai báo dữ liệu
tu_banh_mi = ["1m", "1m2"]
tu_chen = ["80", "1m", "1m2"]
san_pham = ["tu_chen", "be_ca", "tu_trung_bay", "tu_de_ban", "tu_banh_mi"]
vi_tri_dang_bai = ["marketplaces", "cho_tot", "group_fb", "fanpage", "homepage"]
dinh_dang = ["video", "post-image"]
khach = ["den_tiem", "goi_dien", "nhan_tin"]

plugin_info = {
    "enabled": True,
    "methods": [],
    "classes": [],
    "description": "tạo ra tổ hợp từ các mảng",
    "register": lambda assistant: assistant.handlers.insert(3, GenerateActionHandler(assistant))
}

# Lệnh: tạo hành động cho tu_banh_mi
class GenerateActionHandler:
    def __init__(self, assistant):
        self.assistant = assistant

    def can_handle(self, command: str) -> bool:
        return command.strip().lower().startswith("tạo hành động cho")

    def handle(self, command: str) -> bool:
        parts = command.strip().lower().split("cho")
        if len(parts) != 2:
            print("⚠️ Cú pháp: tạo hành động cho <tên sản phẩm>")
            return True

        product_name = parts[1].strip()
        if product_name not in globals():
            print(f"❌ Không tìm thấy danh sách sản phẩm có tên: {product_name}")
            return True

        sizes = globals()[product_name]
        actions = self.generate_actions(product_name, sizes)

        print(f"📋 Đã tạo {len(actions)} hành động cho '{product_name}':\n")
        for i, action in enumerate(actions, 1):
            print(f"{i:02d}. {action}")

        return True

    def generate_actions(self, product: str, sizes: List[str]) -> List[str]:
        result = []
        for size in sizes:
            for format in dinh_dang:
                for location in vi_tri_dang_bai:
                    for customer in khach:
                        action = f"{format} {product} {size} trên {location} → khách {customer}"
                        result.append(action)
        return result