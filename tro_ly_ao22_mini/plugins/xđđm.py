#sd:
# grid start 100
#grid price 85
#grid price 78.625
#grid history
#grid summary
# plugins/dynamic_limit_grid.py

from typing import Any, Optional

# ==============================
# CORE STRATEGY (từ mã 2)
# ==============================
class DynamicLimitGridStrategy:
    def __init__(
        self,
        first_price: float,
        alpha: float = 0.15,
        buy_size: float = 100,
        max_buys: int = 10,
        eps_ratio: float = 0.0005
    ):
        self.alpha = alpha
        self.buy_size = buy_size
        self.max_buys = max_buys
        self.eps_ratio = eps_ratio

        self.total_qty = buy_size
        self.total_cost = first_price * buy_size
        self.avg_price = first_price
        self.buy_count = 1

        self.pending_orders = {}

        self.history = [{
            "buy_no": 1,
            "price": first_price,
            "avg_price": self.avg_price,
            "total_qty": self.total_qty,
            "total_cost": self.total_cost
        }]

        self.place_limit_orders()

    def place_limit_orders(self):
        self.pending_orders = {
            "down": self.avg_price * (1 - self.alpha),
            "up":   self.avg_price * (1 + self.alpha)
        }

    def on_price_update(self, market_price: float):
        if self.buy_count >= self.max_buys:
            return

        eps = self.avg_price * self.eps_ratio

        for target_price in self.pending_orders.values():
            if abs(market_price - target_price) <= eps:
                self.execute_buy(target_price)
                break

    def execute_buy(self, buy_price: float):
        self.buy_count += 1
        self.total_qty += self.buy_size
        self.total_cost += buy_price * self.buy_size
        self.avg_price = self.total_cost / self.total_qty

        self.history.append({
            "buy_no": self.buy_count,
            "price": buy_price,
            "avg_price": self.avg_price,
            "total_qty": self.total_qty,
            "total_cost": self.total_cost
        })

        self.place_limit_orders()

    def print_history(self):
        print("\n=== LỊCH SỬ KHỚP LỆNH ===")
        for h in self.history:
            print(
                f"Lần {h['buy_no']:>2} | "
                f"Giá mua: {h['price']:>8.4f} | "
                f"Giá vốn: {h['avg_price']:>8.4f} | "
                f"Tổng SL: {h['total_qty']:>6}"
            )

    def summary(self):
        print("\n=== TỔNG KẾT ===")
        print(f"Số lần mua: {self.buy_count}")
        print(f"Tổng khối lượng: {self.total_qty}")
        print(f"Tổng vốn: {self.total_cost:.2f}")
        print(f"Giá vốn trung bình: {self.avg_price:.4f}")
        print("Lệnh chờ hiện tại:")
        for k, v in self.pending_orders.items():
            print(f"  {k}: {v:.4f}")


# ==============================
# PLUGIN HANDLER
# ==============================
class DynamicGridHandler:
    def __init__(self, assistant: Any):
        self.assistant = assistant
        self.strategy: Optional[DynamicLimitGridStrategy] = None

    def can_handle(self, command: str) -> bool:
        return command.startswith("grid ")

    def handle(self, command: str) -> None:
        parts = command.split()

        if parts[1] == "start":
            price = float(parts[2])
            self.strategy = DynamicLimitGridStrategy(first_price=price)
            print(f"✅ Khởi tạo Grid tại giá {price}")

        elif parts[1] == "price":
            if not self.strategy:
                print("⚠️ Grid chưa được khởi tạo")
                return
            market_price = float(parts[2])
            self.strategy.on_price_update(market_price)
            print(f"📈 Cập nhật giá thị trường: {market_price}")

        elif parts[1] == "history":
            if self.strategy:
                self.strategy.print_history()

        elif parts[1] == "summary":
            if self.strategy:
                self.strategy.summary()

        else:
            print("❓ Lệnh grid không hợp lệ")


# ==============================
# PLUGIN INFO
# ==============================
def register(assistant: Any):
    assistant.handlers.append(DynamicGridHandler(assistant))

plugin_info = {
    "enabled": True,
    "register": register,
    "command_handle": ["grid"]
}