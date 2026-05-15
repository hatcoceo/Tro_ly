# plugins/bang_excel_bat_tat.py

import random

plugin_info = {
    "enabled": True,
    "register": lambda assistant: assistant.handlers.append(ExcelGridPlugin()),
    "command_handle":[
    "bật 1 2",
    "bật 2 2",
    "bật 3 2",
    "next",
    "đảo 3 2"
    ]
}


class ExcelGridPlugin:

    def __init__(self):

        self.rows = 10
        self.cols = 10

        # bảng chính
        self.grid = [
            [0 for _ in range(self.cols)]
            for _ in range(self.rows)
        ]

    def can_handle(self, command: str) -> bool:

        command = command.lower()

        return (
            command == "bảng"
            or command == "next"
            or command == "random"
            or command.startswith("bật ")
            or command.startswith("tắt ")
            or command.startswith("đảo ")
        )

    def handle(self, command: str):

        command = command.lower()

        # hiển thị bảng
        if command == "bảng":

            print("=== BẢNG HIỆN TẠI ===")
            self.print_grid()

            return True

        # random bảng
        if command == "random":

            for r in range(self.rows):
                for c in range(self.cols):
                    self.grid[r][c] = random.randint(0, 1)

            print("=== RANDOM ===")
            self.print_grid()

            return True

        # chạy game of life
        if command == "next":

            print("=== BẢNG CŨ ===")
            self.print_grid()

            # bảng số hàng xóm
            neighbors_map = [
                [0 for _ in range(self.cols)]
                for _ in range(self.rows)
            ]

            # tính số hàng xóm
            for r in range(self.rows):
                for c in range(self.cols):

                    neighbors_map[r][c] = self.count_neighbors(r, c)

            print("=== SỐ HÀNG XÓM ===")
            self.print_number_grid(neighbors_map)

            # bảng mới
            new_grid = [
                [0 for _ in range(self.cols)]
                for _ in range(self.rows)
            ]

            # áp dụng luật
            for r in range(self.rows):
                for c in range(self.cols):

                    neighbors = neighbors_map[r][c]

                    # ô đang sống
                    if self.grid[r][c] == 1:

                        # sống tiếp
                        if neighbors in [2, 3]:
                            new_grid[r][c] = 1

                        # chết
                        else:
                            new_grid[r][c] = 0

                    # ô đang chết
                    else:

                        # sinh ra
                        if neighbors == 3:
                            new_grid[r][c] = 1

            print("=== BẢNG MỚI ===")

            self.grid = new_grid

            self.print_grid()

            return True

        # bật / tắt / đảo
        try:

            parts = command.split()

            action = parts[0]

            row = int(parts[1])
            col = int(parts[2])

            if not (0 <= row < 10 and 0 <= col < 10):
                print("❌ Tọa độ phải từ 0-9")
                return True

            # bật
            if action == "bật":
                self.grid[row][col] = 1

            # tắt
            elif action == "tắt":
                self.grid[row][col] = 0

            # đảo
            elif action == "đảo":
                self.grid[row][col] = 1 - self.grid[row][col]

            self.print_grid()

        except:

            print("❌ Cú pháp:")
            print("bật row col")
            print("tắt row col")
            print("đảo row col")

        return True

    # đếm hàng xóm sống
    def count_neighbors(self, row, col):

        total = 0

        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:

                # bỏ qua chính nó
                if dr == 0 and dc == 0:
                    continue

                nr = row + dr
                nc = col + dc

                # kiểm tra biên
                if 0 <= nr < self.rows and 0 <= nc < self.cols:

                    total += self.grid[nr][nc]

        return total

    # in bảng 0/1 đẹp
    def print_grid(self):

        print()

        for row in self.grid:

            line = ""

            for cell in row:

                if cell == 1:
                    line += "█ "
                else:
                    line += ". "

            print(line)

        print()

    # in bảng số
    def print_number_grid(self, grid):

        print()

        for row in grid:

            line = ""

            for value in row:
                line += str(value) + " "

            print(line)

        print()