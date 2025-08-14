# sd1: học văn bản du_lieu.txt
# sd : dự đoán từ t
import re
import os
import json
import random
from collections import defaultdict, Counter

MODEL_PATH = "char_markov_model2.json"

plugin_info = {
    "enabled": True,
    "register": lambda assistant: assistant.handlers.insert(1, NextCharWordPredictorHandler(assistant)),
    "methods": [],
    "classes": []
}

class NextCharWordPredictorHandler:
    def __init__(self, assistant):
        self.assistant = assistant
        self.model = defaultdict(Counter)  # model[prefix] = {next_char: count}
        self.words = set()
        self._load_model()

    def _tokenize_words(self, text):
        # Tách từ gồm chữ cái tiếng Việt (không lấy số, dấu câu)
        return re.findall(r"\b\w+\b", text.lower())

    def _build_char_model_from_words(self, word_list):
        for word in word_list:
            if len(word) < 2:
                continue
            self.words.add(word)
            for i in range(1, len(word)):
                prefix = word[:i]
                next_char = word[i]
                self.model[prefix][next_char] += 1

    def _predict_word(self, prefix, max_len=20):
        result = prefix
        for _ in range(max_len):
            options = self.model.get(result)
            if not options:
                break
            next_char = random.choices(list(options.keys()), weights=options.values())[0]
            result += next_char
            if result in self.words:
                return result
        return result  # Trả về nếu không khớp từ hoàn chỉnh

    def _save_model(self):
        try:
            data = {
                "model": {k: dict(v) for k, v in self.model.items()},
                "words": list(self.words)
            }
            with open(MODEL_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"💾 Mô hình đã được lưu vào '{MODEL_PATH}'")
        except Exception as e:
            print(f"❌ Không thể lưu mô hình: {e}")

    def _load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.words = set(data.get("words", []))
                for prefix, counter in data.get("model", {}).items():
                    self.model[prefix] = Counter(counter)
                print(f"📥 Đã nạp mô hình từ '{MODEL_PATH}'")
            except Exception as e:
                print(f"⚠️ Không thể nạp mô hình: {e}")

    def can_handle(self, command: str) -> bool:
        return command.startswith("học văn bản ") or command.startswith("dự đoán từ ")

    def handle(self, command: str) -> bool:
        if command.startswith("học văn bản "):
            path = command[len("học văn bản "):].strip()
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                word_list = self._tokenize_words(text)
                self._build_char_model_from_words(word_list)
                self._save_model()
                print(f"✅ Đã học {len(word_list)} từ từ văn bản '{path}'.")
            except Exception as e:
                print(f"❌ Không đọc được file: {e}")
            return True

        if command.startswith("dự đoán từ "):
            prefix = command[len("dự đoán từ "):].strip().lower()
            result = self._predict_word(prefix)
            if result != prefix:
                print(f"🔮 Dự đoán từ hoàn chỉnh: {result}")
            else:
                print("🤷 Không đủ dữ liệu để dự đoán.")
            return True

        return False