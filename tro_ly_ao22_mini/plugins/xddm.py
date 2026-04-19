#  grid history hiển thị lịch sử khớp thuộc hàng nào cột nào trong ở dữ liệu excel 
"""
Plugin chiến lược lưới giới hạn động (Dynamic Limit Grid Strategy)
============================================================
Mô tả:
    - Chiến lược mua lưới với hai lệnh chờ: mua khi giá giảm (down) và mua khi giá tăng (up).
    - Giá mua trung bình được cập nhật sau mỗi lần khớp lệnh.
    - Hỗ trợ cập nhật giá thủ công từng bước hoặc batch từ file Excel.
    - Hỗ trợ dữ liệu OHLC (Open, High, Low, Close) – cập nhật theo thứ tự Open -> High -> Low -> Close.
    - **Tính năng mới**: Lịch sử hiển thị rõ mỗi lệnh khớp đến từ batch (dòng nào, cột nào) hay lệnh thủ công.
Yêu cầu thư viện:
    pip install pandas openpyxl
"""

import pandas as pd
from typing import Any, Optional, Dict

# ==============================
# LỚP CHIẾN LƯỢC LƯỚI ĐỘNG
# ==============================
class DynamicLimitGridStrategy:
    """
    Triển khai chiến lược lưới giới hạn động.
    
    Nguyên lý:
        - Sau mỗi lần mua, giá vốn trung bình (avg_price) được tính lại.
        - Hai lệnh chờ được đặt:
            * down: giá mua khi thị trường giảm = avg_price * (1 - alpha)
            * up:   giá mua khi thị trường tăng = avg_price * (1 + alpha)
        - Khi giá thị trường chạm vào một trong hai mức (trong phạm vi eps), lệnh được thực hiện.
        - Lịch sử giao dịch được lưu lại kèm thông tin nguồn (batch/manual).
    """

    def __init__(
        self,
        first_price: float,
        alpha: float = 0.15,
        buy_size: float = 100,
        eps_ratio: float = 0.01
    ):
        """
        Khởi tạo chiến lược với lần mua đầu tiên.
        
        Tham số:
            first_price: Giá mua ban đầu (khởi tạo)
            alpha: Biên độ lưới (ví dụ 0.15 = ±15%)
            buy_size: Khối lượng mỗi lần mua (cố định)
            eps_ratio: Tỷ lệ dung sai (epsilon) so với avg_price, dùng để so khớp giá
        """
        self.alpha = alpha
        self.buy_size = buy_size
        self.eps_ratio = eps_ratio

        self.total_qty = buy_size
        self.total_cost = first_price * buy_size
        self.avg_price = round(first_price, 2)
        self.buy_count = 1

        self.pending_orders = {}
        # Lịch sử: mỗi phần tử là dict, bổ sung trường "source"
        self.history = [{
            "buy_no": 1,
            "price": round(first_price, 2),
            "avg_price": self.avg_price,
            "total_qty": self.total_qty,
            "total_cost": self.total_cost,
            "side": "init",
            "source": {"type": "init"}          # nguồn khởi tạo
        }]
        self.place_limit_orders()

    def place_limit_orders(self):
        """Tính lại các mức giá lệnh chờ dựa trên giá vốn trung bình hiện tại."""
        self.pending_orders = {
            "down": round(self.avg_price * (1 - self.alpha), 2),
            "up":   round(self.avg_price * (1 + self.alpha), 2)
        }

    def on_price_update(self, market_price: float, source_info: Optional[Dict] = None):
        """
        Xử lý khi có giá thị trường mới.
        
        Tham số:
            market_price: Giá thị trường hiện tại
            source_info (dict, optional): Thông tin nguồn gốc của giá này.
                - Nếu từ batch: {"type": "batch", "row": int, "col": str}
                - Nếu từ lệnh manual: {"type": "manual"}
        """
        market_price_rounded = round(market_price, 2)
        eps = self.avg_price * self.eps_ratio

        for side, target_price in self.pending_orders.items():
            if abs(market_price_rounded - target_price) <= eps:
                self.execute_buy(target_price, side, source_info)
                break

    def execute_buy(self, buy_price: float, side: str, source_info: Optional[Dict] = None):
        """
        Thực hiện mua với giá và hướng (up/down) đã khớp.
        
        Tham số:
            buy_price: Giá khớp lệnh
            side: "up" hoặc "down"
            source_info: Thông tin nguồn (được lưu vào lịch sử)
        """
        self.buy_count += 1
        self.total_qty += self.buy_size
        self.total_cost += buy_price * self.buy_size
        self.avg_price = round(self.total_cost / self.total_qty, 2)

        # Mặc định nếu không có source_info thì gán là manual (để tương thích cũ)
        if source_info is None:
            source_info = {"type": "manual"}

        self.history.append({
            "buy_no": self.buy_count,
            "price": round(buy_price, 2),
            "avg_price": self.avg_price,
            "total_qty": self.total_qty,
            "total_cost": self.total_cost,
            "side": side,
            "source": source_info
        })
        self.place_limit_orders()

    # === Các phương thức thống kê và báo cáo ===

    def print_history(self):
        """In lịch sử các lần mua, kèm thông tin nguồn gốc (dòng/cột hoặc manual)."""
        print("\n=== LỊCH SỬ KHỚP LỆNH (kèm nguồn) ===")
        # Header
        print(f"{'Lần':>4} | {'Hướng':>5} | {'Giá mua':>8} | {'Giá vốn':>8} | {'Tổng SL':>7} | Nguồn")
        print("-" * 70)
        for h in self.history:
            # Định dạng thông tin nguồn
            src = h["source"]
            if src["type"] == "init":
                source_str = "Khởi tạo"
            elif src["type"] == "manual":
                source_str = "Lệnh thủ công"
            elif src["type"] == "batch":
                source_str = f"Batch: dòng {src['row']}, cột {src['col'].upper()}"
            else:
                source_str = "Khác"
            
            print(
                f"{h['buy_no']:>4} | "
                f"{h['side']:>5} | "
                f"{h['price']:>8.2f} | "
                f"{h['avg_price']:>8.2f} | "
                f"{h['total_qty']:>7} | {source_str}"
            )

    def count_up_down(self):
        """Đếm số lần mua theo hướng up và down (bỏ qua lần init)."""
        up = sum(1 for h in self.history if h["side"] == "up")
        down = sum(1 for h in self.history if h["side"] == "down")
        return up, down

    def up_down_ratio(self):
        up, down = self.count_up_down()
        if down == 0:
            return float('inf')
        return up / down

    def up_down_score(self):
        up, down = self.count_up_down()
        total = up + down
        if total == 0:
            return 0
        return (up - down) / total

    def flip_rate(self):
        sides = [h["side"] for h in self.history if h["side"] in ("up", "down")]
        flips = 0
        for i in range(1, len(sides)):
            if sides[i] != sides[i-1]:
                flips += 1
        if len(sides) <= 1:
            return 0
        return flips / (len(sides) - 1)

    def avg_streak_length(self):
        sides = [h["side"] for h in self.history if h["side"] in ("up", "down")]
        if not sides:
            return 0
        streaks = []
        current = 1
        for i in range(1, len(sides)):
            if sides[i] == sides[i-1]:
                current += 1
            else:
                streaks.append(current)
                current = 1
        streaks.append(current)
        return sum(streaks) / len(streaks)

    def summary(self):
        up, down = self.count_up_down()
        print("\n=== TỔNG KẾT ===")
        print(f"Số lần mua: {self.buy_count}")
        print(f"Tổng khối lượng: {self.total_qty}")
        print(f"Tổng vốn: {self.total_cost:.2f}")
        print(f"Giá vốn trung bình: {self.avg_price:.2f}")
        print("\n--- Up/Down ---")
        print(f"Up: {up}")
        print(f"Down: {down}")
        print(f"Ratio: {self.up_down_ratio():.4f}")
        print(f"Score: {self.up_down_score():.4f}")
        print("\n--- Market Structure ---")
        print(f"Flip rate: {self.flip_rate():.4f}")
        print(f"Avg streak: {self.avg_streak_length():.4f}")
        print("\n--- Pending Orders ---")
        for k, v in self.pending_orders.items():
            print(f"{k}: {v:.2f}")


# ==============================
# HANDLER TÍCH HỢP VỚI VIRTUALASSISTANT
# ==============================
class DynamicGridHandler:
    """Handler xử lý các lệnh grid."""

    def __init__(self):
        self.strategy: Optional[DynamicLimitGridStrategy] = None

    def can_handle(self, command: str) -> bool:
        return command.startswith("grid ")

    def handle(self, command: str) -> None:
        parts = command.strip().split()
        if len(parts) < 2:
            print("⚠️ Lệnh grid cần có tham số. Gõ 'grid help' để xem hướng dẫn.")
            return

        sub = parts[1].lower()

        if sub == "create":
            if len(parts) != 5:
                print("⚠️ Cú pháp: grid create <giá_đầu> <alpha> <buy_size>")
                return
            try:
                first_price = float(parts[2])
                alpha = float(parts[3])
                buy_size = float(parts[4])
                self.strategy = DynamicLimitGridStrategy(first_price, alpha, buy_size)
                print(f"✅ Đã tạo chiến lược mới: giá đầu={first_price:.2f}, alpha={alpha}, size={buy_size}")
            except ValueError:
                print("⚠️ Tham số không hợp lệ. Vui lòng nhập số.")

        elif sub == "update":
            if self.strategy is None:
                print("⚠️ Chưa có chiến lược. Hãy tạo bằng 'grid create ...'")
                return
            if len(parts) != 3:
                print("⚠️ Cú pháp: grid update <giá_thị_trường>")
                return
            try:
                price = float(parts[2])
                # Gọi với source_info là manual
                self.strategy.on_price_update(price, source_info={"type": "manual"})
                print(f"🔄 Đã cập nhật giá {price:.2f} (thủ công)")
            except ValueError:
                print("⚠️ Giá không hợp lệ.")

        elif sub == "batch":
            if self.strategy is None:
                print("⚠️ Chưa có chiến lược. Hãy tạo bằng 'grid create ...'")
                return
            if len(parts) != 3:
                print("⚠️ Cú pháp: grid batch <đường_dẫn_file_excel>")
                return
            file_path = parts[2]
            self._handle_batch(file_path)

        elif sub == "history":
            if self.strategy is None:
                print("⚠️ Chưa có chiến lược.")
                return
            self.strategy.print_history()

        elif sub == "summary":
            if self.strategy is None:
                print("⚠️ Chưa có chiến lược.")
                return
            self.strategy.summary()

        elif sub == "stats":
            if self.strategy is None:
                print("⚠️ Chưa có chiến lược.")
                return
            up, down = self.strategy.count_up_down()
            print("\n=== THỐNG KÊ NHANH ===")
            print(f"Up/Down Ratio : {self.strategy.up_down_ratio():.4f}")
            print(f"Up/Down Score : {self.strategy.up_down_score():.4f}")
            print(f"Flip rate     : {self.strategy.flip_rate():.4f}")
            print(f"Avg streak len: {self.strategy.avg_streak_length():.4f}")

        elif sub == "pending":
            if self.strategy is None:
                print("⚠️ Chưa có chiến lược.")
                return
            print("\n--- Lệnh chờ ---")
            for k, v in self.strategy.pending_orders.items():
                print(f"{k}: {v:.2f}")

        elif sub == "help":
            print("""
Hướng dẫn lệnh grid:
  grid create <giá_đầu> <alpha> <size>  - Tạo chiến lược mới
  grid update <giá>                     - Cập nhật giá thủ công
  grid batch <đường_dẫn_file_excel>    - Cập nhật hàng loạt từ file (OHLC: Open→High→Low→Close)
  grid history                          - Xem lịch sử mua (kèm nguồn: dòng/cột)
  grid summary                          - Xem tổng kết chi tiết
  grid stats                            - Xem các chỉ số đánh giá
  grid pending                          - Xem lệnh chờ (up/down)
  grid help                             - Hiển thị hướng dẫn này
""")
        else:
            print(f"⚠️ Không rõ lệnh '{sub}'. Gõ 'grid help' để xem hướng dẫn.")

    def _handle_batch(self, file_path: str) -> None:
        """
        Xử lý batch từ file Excel, hỗ trợ OHLC.
        Mỗi lần cập nhật giá đều gắn source_info chứa số dòng và loại cột.
        """
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            print(f"❌ Không thể đọc file: {e}")
            return

        cols = {col.lower(): col for col in df.columns}
        close_col = cols.get('close')
        open_col = cols.get('open')
        high_col = cols.get('high')
        low_col = cols.get('low')

        if close_col is None:
            print("⚠️ Không tìm thấy cột 'close' trong file.")
            print(f"Các cột có: {list(df.columns)}")
            return

        # Thứ tự ưu tiên: open, high, low, close
        price_columns = []
        if open_col:
            price_columns.append(('open', open_col))
        if high_col:
            price_columns.append(('high', high_col))
        if low_col:
            price_columns.append(('low', low_col))
        price_columns.append(('close', close_col))

        total_rows = len(df)
        print(f"📊 Đọc được {total_rows} dòng. Sẽ cập nhật theo thứ tự: {[p[0] for p in price_columns]}")
        
        for idx, row in df.iterrows():
            row_num = idx + 1   # Dòng bắt đầu từ 1 cho dễ đọc
            for price_type, col_name in price_columns:
                price_val = row[col_name]
                if pd.isna(price_val):
                    continue
                try:
                    source_info = {
                        "type": "batch",
                        "row": row_num,
                        "col": price_type
                    }
                    self.strategy.on_price_update(float(price_val), source_info=source_info)
                    print(f"  [dòng {row_num}/{total_rows}] {price_type.upper()}={price_val:.2f} -> đã cập nhật")
                except Exception as e:
                    print(f"  ⚠️ Lỗi tại {price_type.upper()}={price_val:.2f}: {e}")

        print("✅ Hoàn tất batch update.")
        self.strategy.summary()


# ==============================
# THÔNG TIN PLUGIN (BẮT BUỘC)
# ==============================
plugin_info = {
    "enabled": True,
    "register": lambda assistant: assistant.handlers.append(DynamicGridHandler()),
    "command_handle": ["grid"]
}