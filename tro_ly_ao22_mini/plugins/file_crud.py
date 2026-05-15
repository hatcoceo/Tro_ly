import os
import shutil
import time
from typing import Any, List

BASE_DIR = os.getcwd()  # 👈 thư mục chạy chương trình
TRASH_DIR = os.path.join(BASE_DIR, ".trash")

os.makedirs(TRASH_DIR, exist_ok=True)


class ProjectFileHandler:
    def __init__(self, assistant: Any):
        self.assistant = assistant
        self.history: List[dict] = []

    def _safe_path(self, path: str) -> str:
        full = os.path.abspath(os.path.join(BASE_DIR, path))
        if not full.startswith(BASE_DIR):
            raise ValueError("❌ Không được truy cập ra ngoài project")
        return full

    def can_handle(self, command: str) -> bool:
        return command.startswith((
            "pcreate ", "pread ", "pupdate ", "pdelete ",
            "pls", "pmkdir ", "pundo", "prestore"
        ))

    def handle(self, command: str):
        parts = command.split()
        cmd = parts[0]

        try:
            if cmd == "pcreate":
                path = self._safe_path(parts[1])
                content = " ".join(parts[2:])

                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                    return path  # 👈 THÊM DÒNG NÀY

                self.history.append({"action": "delete", "path": path})
                print(f"📄 Tạo file: {path}")

            elif cmd == "pread":
                path = self._safe_path(parts[1])
                if not os.path.exists(path):
                    print("❌ Không tồn tại")
                    return

                with open(path, "r", encoding="utf-8") as f:
                    print("📖\n" + f.read())

            elif cmd == "pupdate":
                path = self._safe_path(parts[1])
                content = " ".join(parts[2:])

                if not os.path.exists(path):
                    print("❌ Không tồn tại")
                    return

                with open(path, "r", encoding="utf-8") as f:
                    old = f.read()

                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)

                self.history.append({"action": "update", "path": path, "old": old})
                print("✏️ Đã cập nhật")

            elif cmd == "pdelete":
                path = self._safe_path(parts[1])

                if not os.path.exists(path):
                    print("❌ Không tồn tại")
                    return

                name = os.path.basename(path)
                trash_path = os.path.join(TRASH_DIR, f"{int(time.time())}_{name}")

                shutil.move(path, trash_path)
                self.history.append({"action": "restore", "src": trash_path, "dst": path})

                print("🗑️ Đã chuyển vào .trash")

            elif cmd == "prestore":
                files = os.listdir(TRASH_DIR)
                if not files:
                    print("📭 Trash trống")
                    return

                latest = sorted(files)[-1]
                src = os.path.join(TRASH_DIR, latest)
                dst = self._safe_path(latest.split("_", 1)[1])

                shutil.move(src, dst)
                print("♻️ Đã restore")

            elif cmd == "pls":
                path = self._safe_path(parts[1]) if len(parts) > 1 else BASE_DIR
                files = os.listdir(path) # thêm biến này vào để macro lấy giá trị return 

                #print("📂 Files:")
                #for f in os.listdir(path):
                    #print(" -", f)
                
                return files  # 👈 thêm dòng này nữa 
            elif cmd == "pmkdir":
                path = self._safe_path(parts[1])
                os.makedirs(path, exist_ok=True)
                print("📁 Đã tạo folder")
                return path  # 👈 lấy return của file mới vừa tạo

            elif cmd == "pundo":
                if not self.history:
                    print("⏪ Nothing to undo")
                    return

                last = self.history.pop()

                if last["action"] == "delete":
                    if os.path.exists(last["path"]):
                        os.remove(last["path"])
                    print("⏪ Undo create")

                elif last["action"] == "update":
                    with open(last["path"], "w", encoding="utf-8") as f:
                        f.write(last["old"])
                    print("⏪ Undo update")

                elif last["action"] == "restore":
                    if os.path.exists(last["dst"]):
                        shutil.move(last["dst"], last["src"])
                    print("⏪ Undo delete")

            else:
                print("⚠️ Lệnh không hợp lệ")

        except Exception as e:
            print(f"⚠️ Lỗi: {e}")


def register(assistant: Any):
    assistant.handlers.append(ProjectFileHandler(assistant))


plugin_info = {
    "enabled": True,
    "register": register,
    "command_handle": [
        "pcreate", "pread", "pupdate", "pdelete",
        "pls", "pmkdir", "pundo", "prestore"
    ]
}