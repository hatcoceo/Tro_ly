# sử dụng :
# gộp json events1.json events2.json
import json
from typing import List, Dict
from __main__  import ICommandHandler  # đảm bảo bạn đã có interfaces/ICommandHandler.py hoặc tương đương


class JsonMerger:
    def merge_events(self, file1: str, file2: str, output_file: str = "events.json") -> None:
        events1 = self._load_json(file1)
        events2 = self._load_json(file2)

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
        return command.strip().lower().startswith("gộp json")

    def handle(self, command: str) -> bool:
        parts = command.strip().split()
        if len(parts) < 4:
            print("⚠️ Cú pháp đúng: gộp json <file1> <file2> [output_file]")
            return True

        file1 = parts[2]
        file2 = parts[3]
        output = parts[4] if len(parts) > 4 else "merged_events.json"

        self.assistant.call_method("JsonMerger", "merge_events", file1, file2, output, version="v1")
        return True


# ==== Plugin Info ====

def register(assistant):
    # Đăng ký class + method
    assistant.version_manager.register_class_version(
        class_name="JsonMerger",
        version="v1",
        class_ref=JsonMerger
    )

    assistant.version_manager.register_method_version(
        class_name="JsonMerger",
        method_name="merge_events",
        version="v1",
        method_ref=JsonMerger().merge_events,
        description="Hợp nhất 2 file JSON chứa sự kiện.",
        mode="replace"
    )

    # Đăng ký handler
    assistant.handlers.insert (2, MergeJsonHandler(assistant))


plugin_info = {
    "enabled": False,
    "register": register,
    "methods": [],
    "classes": []
}