# sử dụng :
# gộp json events1.json su_kien.txt events.json
import json
import os
from typing import List, Dict
from datetime import datetime
from __main__  import ICommandHandler


class JsonMerger:
    def merge_events(self, file1: str, file2: str, output_file: str = "merged_events.json") -> None:
        events1 = self._load_file(file1)
        events2 = self._load_file(file2)

        seen = set()
        merged = []

        for event in events1 + events2:
            key = f"{event.get('content', '').strip()}|{event.get('date', '').strip()}"
            if key not in seen:
                seen.add(key)
                merged.append(event)

        merged.sort(key=lambda x: x.get("date", ""))
        self._save_json(merged, output_file)

        print(f"✅ Đã hợp nhất {len(events1)} + {len(events2)} sự kiện thành {len(merged)} dòng trong '{output_file}'.")

    def _load_file(self, path: str) -> List[Dict]:
        ext = os.path.splitext(path)[-1].lower()
        if ext == ".json":
            return self._load_json(path)
        elif ext == ".txt":
            return self._load_txt(path)
        else:
            print(f"⚠️ Không hỗ trợ định dạng: {ext}")
            return []

    def _load_json(self, path: str) -> List[Dict]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                print(f"⚠️ {path} không chứa danh sách JSON.")
                return []
        except Exception as e:
            print(f"❌ Lỗi đọc {path}: {e}")
            return []

    def _load_txt(self, path: str) -> List[Dict]:
        events = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "||" not in line:
                        continue
                    parts = line.split("||", 1)
                    date_str = parts[0].strip()
                    content = parts[1].strip()
                    try:
                        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                        iso_date = dt.isoformat()
                        events.append({"content": content, "date": iso_date})
                    except Exception:
                        print(f"⚠️ Dòng sai định dạng ngày giờ: {line}")
        except Exception as e:
            print(f"❌ Lỗi đọc {path}: {e}")
        return events

    def _save_json(self, data: List[Dict], path: str) -> None:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ Lỗi ghi {path}: {e}")


class MergeJsonHandler(ICommandHandler):
    def __init__(self, assistant):
        self.assistant = assistant

    def can_handle(self, command: str) -> bool:
        return command.lower().startswith("gộp json")

    def handle(self, command: str) -> bool:
        parts = command.strip().split()
        if len(parts) < 4:
            print("⚠️ Cú pháp: gộp json <file1> <file2> [output_file]")
            return True

        file1 = parts[2]
        file2 = parts[3]
        output = parts[4] if len(parts) > 4 else "merged_events.json"

        self.assistant.call_method("JsonMerger", "merge_events", file1, file2, output)
        return True


# ==== Đăng ký plugin ====

def register(assistant):
    for version in ["default", "v1"]:
        assistant.version_manager.register_class_version("JsonMerger", version, JsonMerger)
        assistant.version_manager.register_method_version(
            "JsonMerger",
            "merge_events",
            version,
            JsonMerger().merge_events,
            description="Hợp nhất 2 file JSON hoặc TXT chứa sự kiện.",
            mode="replace"
        )

    assistant.handlers.insert (3, MergeJsonHandler(assistant))


plugin_info = {
    "enabled": True,
    "register": register,
    "methods": [],
    "classes": []
}