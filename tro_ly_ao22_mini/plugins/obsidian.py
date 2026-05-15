# plugins/obsidian_plugin.py
import os
import re
import json
import platform
import webbrowser
from urllib.parse import quote
from typing import Optional, Dict, Any, List

# -------------------- CẤU HÌNH --------------------
CONFIG_DIR = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(CONFIG_DIR, "obsidian_config.json")

DEFAULT_CONFIG = {
    "vaults": [],
    "default_vault": ""
}

def normalize_path(path: str) -> str:
    """Chuẩn hóa đường dẫn, xử lý ~ và Android Termux"""
    path = os.path.expanduser(path)
    if platform.system() == "Linux" and "/storage/emulated/0" in path:
        # Có thể đang chạy trong Termux trên Android
        if not os.path.exists(path):
            print(f"⚠️ Đường dẫn {path} không tồn tại. Trên Termux, hãy chạy 'termux-setup-storage' và thử lại.")
    return os.path.abspath(path)

def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any]):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def find_vault_path(vault_name: str, config: Dict) -> Optional[str]:
    for v in config.get("vaults", []):
        if v["name"].lower() == vault_name.lower():
            return v["path"]
    return None

def list_markdown_files(vault_path: str) -> List[str]:
    md_files = []
    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '.obsidian']
        for file in files:
            if file.endswith(".md"):
                rel_path = os.path.relpath(os.path.join(root, file), vault_path)
                md_files.append(rel_path)
    return md_files

def read_note_content(vault_path: str, note_path: str) -> Optional[str]:
    full_path = os.path.join(vault_path, note_path)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Lỗi đọc file: {e}"
    return None

def write_note_content(vault_path: str, note_path: str, content: str) -> bool:
    full_path = os.path.join(vault_path, note_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"❌ Lỗi ghi file: {e}")
        return False

# -------------------- XỬ LÝ LỆNH --------------------
class ObsidianHandler:
    def __init__(self, assistant):
        self.assistant = assistant
        self.config = load_config()
        self.default_vault = self.config.get("default_vault", "")

    def can_handle(self, command: str) -> bool:
        cmd = command.lower()
        triggers = [
            "obsidian", "vault", "ghi chú", "note",
            "mở vault", "open vault", "tạo ghi chú", "create note",
            "mở ghi chú", "open note", "đọc ghi chú", "read note",
            "tìm ghi chú", "find note", "liệt kê ghi chú", "list notes",
            "đặt vault mặc định", "set default vault", "thêm vault", "add vault"
        ]
        return any(t in cmd for t in triggers)

    def handle(self, command: str) -> Optional[bool]:
        cmd = command.lower().strip()

        # 1. Thêm vault mới (tên = đường dẫn)
        if cmd.startswith("thêm vault") or cmd.startswith("add vault"):
            pattern = r"(?:thêm vault|add vault)\s+(.+?)\s*=\s*(.+)$"
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                vault_name = match.group(1).strip()
                vault_path = match.group(2).strip()
                vault_path = normalize_path(vault_path)
                if os.path.isdir(vault_path):
                    existing = [v for v in self.config["vaults"] if v["name"] == vault_name]
                    if existing:
                        print(f"⚠️ Vault '{vault_name}' đã tồn tại. Ghi đè đường dẫn.")
                        existing[0]["path"] = vault_path
                    else:
                        self.config["vaults"].append({"name": vault_name, "path": vault_path})
                    save_config(self.config)
                    print(f"✅ Đã thêm vault '{vault_name}' tại {vault_path}")
                else:
                    print(f"❌ Đường dẫn không hợp lệ hoặc không phải thư mục: {vault_path}")
            else:
                print("⚠️ Cú pháp: thêm vault <tên vault> = <đường dẫn tuyệt đối>")
                print("   Ví dụ: thêm vault Ca = /storage/emulated/0/Documents/Ca")
            return None

        # 2. Đặt vault mặc định
        if cmd.startswith("đặt vault mặc định") or cmd.startswith("set default vault"):
            vault_name = self._extract_vault_name(cmd)
            if not vault_name:
                self._list_vaults()
                return None
            if find_vault_path(vault_name, self.config):
                self.default_vault = vault_name
                self.config["default_vault"] = vault_name
                save_config(self.config)
                print(f"✅ Đã đặt vault mặc định: {vault_name}")
            else:
                print(f"❌ Không tìm thấy vault '{vault_name}'. Hãy thêm vault trước bằng lệnh 'thêm vault'.")
            return None

        # 3. Mở vault (dùng URI)
        if cmd.startswith("mở vault") or cmd.startswith("open vault"):
            vault_name = self._extract_vault_name(cmd)
            if not vault_name:
                vault_name = self.default_vault
                if not vault_name:
                    print("⚠️ Chưa có vault mặc định. Vui lòng chỉ định tên vault hoặc đặt mặc định.")
                    return None
            self._open_obsidian_uri(f"obsidian://open?vault={quote(vault_name)}")
            print(f"📂 Đang mở vault: {vault_name}")
            return None

        # 4. Tạo ghi chú mới
        if cmd.startswith("tạo ghi chú") or cmd.startswith("create note"):
            note_name = self._extract_note_name(cmd)
            if not note_name:
                print("⚠️ Vui lòng nhập tên ghi chú. Ví dụ: 'tạo ghi chú Học tập/ngày 1'")
                return None
            vault_name = self._get_target_vault(cmd)
            if not vault_name:
                return None
            uri = f"obsidian://new?vault={quote(vault_name)}&name={quote(note_name)}"
            self._open_obsidian_uri(uri)
            print(f"📝 Đang tạo ghi chú: {note_name} trong vault {vault_name}")
            return None

        # 5. Mở ghi chú (bằng URI)
        if cmd.startswith("mở ghi chú") or cmd.startswith("open note"):
            note_name = self._extract_note_name(cmd)
            if not note_name:
                print("⚠️ Vui lòng nhập tên ghi chú. Ví dụ: 'mở ghi chú Học tập'")
                return None
            vault_name = self._get_target_vault(cmd)
            if not vault_name:
                return None
            uri = f"obsidian://open?vault={quote(vault_name)}&file={quote(note_name)}"
            self._open_obsidian_uri(uri)
            print(f"📖 Đang mở ghi chú: {note_name}")
            return None

        # 6. Đọc nội dung ghi chú (hiển thị trong terminal)
        if cmd.startswith("đọc ghi chú") or cmd.startswith("read note"):
            note_name = self._extract_note_name(cmd)
            if not note_name:
                print("⚠️ Vui lòng nhập đường dẫn ghi chú (tương đối trong vault). Ví dụ: 'đọc ghi chú Thư mục/ghi chú.md'")
                return None
            vault_name = self._get_target_vault(cmd)
            if not vault_name:
                return None
            vault_path = find_vault_path(vault_name, self.config)
            if not vault_path:
                print(f"❌ Không tìm thấy đường dẫn của vault '{vault_name}'")
                return None
            content = read_note_content(vault_path, note_name)
            if content is not None:
                print(f"\n--- Nội dung ghi chú: {note_name} ---\n{content}\n--- Hết ---")
            else:
                print(f"❌ Không tìm thấy ghi chú: {note_name}")
            return None

        # 7. Liệt kê tất cả ghi chú trong vault
        if cmd.startswith("liệt kê ghi chú") or cmd.startswith("list notes"):
            vault_name = self._get_target_vault(cmd)
            if not vault_name:
                return None
            vault_path = find_vault_path(vault_name, self.config)
            if not vault_path:
                print(f"❌ Không tìm thấy đường dẫn vault '{vault_name}'")
                return None
            files = list_markdown_files(vault_path)
            if files:
                print(f"📄 Các ghi chú trong vault '{vault_name}':")
                for f in files:
                    print(f"  - {f}")
                print(f"Tổng cộng: {len(files)} ghi chú")
            else:
                print(f"📭 Không có file .md nào trong vault '{vault_name}'")
            return None

        # 8. Tìm kiếm ghi chú theo từ khóa (trong nội dung)
        if cmd.startswith("tìm ghi chú") or cmd.startswith("find note"):
            keyword = self._extract_keyword(cmd)
            if not keyword:
                print("⚠️ Vui lòng nhập từ khóa cần tìm. Ví dụ: 'tìm ghi chú python'")
                return None
            vault_name = self._get_target_vault(cmd)
            if not vault_name:
                return None
            vault_path = find_vault_path(vault_name, self.config)
            if not vault_path:
                print(f"❌ Không tìm thấy vault '{vault_name}'")
                return None
            results = []
            for root, dirs, files in os.walk(vault_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '.obsidian']
                for file in files:
                    if file.endswith(".md"):
                        full_path = os.path.join(root, file)
                        try:
                            with open(full_path, "r", encoding="utf-8") as f:
                                content = f.read()
                                if keyword.lower() in content.lower():
                                    rel_path = os.path.relpath(full_path, vault_path)
                                    results.append(rel_path)
                        except:
                            continue
            if results:
                print(f"🔍 Tìm thấy {len(results)} ghi chú chứa '{keyword}' trong vault '{vault_name}':")
                for r in results:
                    print(f"  - {r}")
            else:
                print(f"🔍 Không tìm thấy ghi chú nào chứa '{keyword}'")
            return None

        print("🤷 Lệnh Obsidian không hợp lệ. Gõ 'trợ giúp obsidian' để xem hướng dẫn.")
        return None

    # -------------------- CÁC HÀM TRỢ GIÚP --------------------
    def _extract_vault_name(self, cmd: str) -> str:
        pattern = r"(?:mở vault|open vault|đặt vault mặc định|set default vault)\s+(.+)$"
        match = re.search(pattern, cmd, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _extract_note_name(self, cmd: str) -> str:
        patterns = [
            r"(?:tạo ghi chú|create note|mở ghi chú|open note|đọc ghi chú|read note)\s+(.+?)(?:\s+trong\s+vault|\s*$)",
            r"(?:tạo ghi chú|create note|mở ghi chú|open note|đọc ghi chú|read note)\s+(.+)$"
        ]
        for pat in patterns:
            match = re.search(pat, cmd, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_keyword(self, cmd: str) -> str:
        cmd_clean = re.sub(r"\s+trong\s+vault\s+\S+", "", cmd, flags=re.IGNORECASE)
        pattern = r"(?:tìm ghi chú|find note)\s+(.+)$"
        match = re.search(pattern, cmd_clean, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _get_target_vault(self, cmd: str) -> Optional[str]:
        match = re.search(r"trong\s+vault\s+([^\s]+(?:\s+[^\s]+)*)", cmd, re.IGNORECASE)
        if match:
            vault_name = match.group(1).strip()
            if find_vault_path(vault_name, self.config):
                return vault_name
            else:
                print(f"❌ Không tìm thấy vault '{vault_name}'. Hãy thêm vault bằng lệnh 'thêm vault'.")
                return None
        if self.default_vault:
            if find_vault_path(self.default_vault, self.config):
                return self.default_vault
            else:
                print(f"❌ Vault mặc định '{self.default_vault}' không tồn tại trong cấu hình.")
                return None
        else:
            print("⚠️ Chưa có vault mặc định. Hãy đặt bằng 'đặt vault mặc định <tên>' hoặc chỉ định 'trong vault <tên>'.")
            return None

    def _list_vaults(self):
        if not self.config["vaults"]:
            print("📭 Chưa có vault nào. Hãy thêm bằng lệnh 'thêm vault Tên = /đường/dẫn'")
        else:
            print("📂 Danh sách vault đã biết:")
            for v in self.config["vaults"]:
                default_mark = " (mặc định)" if v["name"] == self.default_vault else ""
                print(f"  - {v['name']}{default_mark}: {v['path']}")

    def _open_obsidian_uri(self, uri: str):
        webbrowser.open(uri)

# -------------------- ĐĂNG KÝ PLUGIN --------------------
plugin_info = {
    "enabled": True,
    "register": lambda assistant: assistant.handlers.append(ObsidianHandler(assistant)),
    "command_handle": [
    "mở vault demo",
"liệt kê ghi chú",
"tạo ghi chú Test",
"đặt vault mặc định demo",
"mở ghi chú tủ thuốc",
"đọc ghi chú demo.md"

]
}