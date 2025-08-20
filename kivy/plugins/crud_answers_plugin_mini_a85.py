import os
from typing import List
import difflib


class KnowledgeManager:

    def __init__(self, similarity_thresh: float=0.6):
        self.file_path = 'tri_thuc.txt'
        self.temp_file = 'delete_candidates.txt'
        self.similarity_thresh = similarity_thresh
        self._ensure_file_exists()
        self.suggestions = []

    def _ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            open(self.file_path, 'w').close()

    def _read_all_lines(self) ->List[str]:
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines() if line.strip()]

    def _write_all_lines(self, lines: List[str]):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def add(self, data: str) ->str:
        with open(self.file_path, 'a', encoding='utf-8') as f:
            f.write(data.strip() + '\n')
        return '✅ Đã thêm dòng kiến thức'

    def read(self) ->str:
        lines = self._read_all_lines()
        if not lines:
            return '📭 Không có dữ liệu.'
        return '\n'.join(f'{i + 1}. {line}' for i, line in enumerate(lines))

    def update(self, line_number: int, new_data: str) ->str:
        lines = self._read_all_lines()
        if line_number < 1 or line_number > len(lines):
            return '❌ Số dòng không hợp lệ.'
        lines[line_number - 1] = new_data.strip()
        self._write_all_lines(lines)
        return f'✅ Đã cập nhật dòng {line_number}.'

    def delete_by_keyword(self, keyword: str) ->str:
        keyword = keyword.strip().lower()
        lines = self._read_all_lines()
        exact_matches = [i for i, line in enumerate(lines) if line.split(
            '||')[0].strip().lower() == keyword]
        if exact_matches:
            for i in sorted(exact_matches, reverse=True):
                del lines[i]
            self._write_all_lines(lines)
            return '🗑️ Đã xóa các dòng phù hợp'
        similar_matches = [(i, line) for i, line in enumerate(lines) if 
            keyword in line.lower()]
        if not similar_matches:
            return '🔎 Không tìm thấy dữ liệu phù hợp để xóa.'
        with open(self.temp_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(line for _, line in similar_matches))
        result = ['🔎 Tìm thấy các dòng gần giống:']
        result.extend(f'{i + 1}. [Dòng {idx + 1}] {line}' for i, (idx, line
            ) in enumerate(similar_matches))
        result.append('👉 Gõ: xóa_chọn:<số thứ tự> để xóa dòng tương ứng.')
        return '\n'.join(result)

    def delete_by_index(self, select_number: int) ->str:
        try:
            with open(self.temp_file, 'r', encoding='utf-8') as f:
                candidates = [line.strip() for line in f.readlines()]
            if select_number < 1 or select_number > len(candidates):
                return '❌ Số thứ tự không hợp lệ.'
            target_line = candidates[select_number - 1]
            lines = self._read_all_lines()
            lines.remove(target_line)
            self._write_all_lines(lines)
            os.remove(self.temp_file)
            return f'🗑️ Đã xóa dòng: {target_line}'
        except Exception as e:
            return f'❌ Lỗi khi xóa: {str(e)}'

    def _match_exact(self, query: str) ->List[str]:
        lines = self._read_all_lines()
        return [ans.strip() for line in lines if (parts := line.split('||',
            1))[0].strip().lower() == query.lower() for ans in [parts[1]]]

    def _match_similar(self, query: str) ->List[str]:
        lines = self._read_all_lines()
        candidates = []
        for line in lines:
            if '||' not in line:
                continue
            question, answer = line.split('||', 1)
            similarity = difflib.SequenceMatcher(None, query.lower(),
                question.lower().strip()).ratio()
            if similarity >= self.similarity_thresh:
                candidates.append(line)
        return candidates

    def get_answer(self, query: str) ->str:
        exact_matches = self._match_exact(query)
        if exact_matches:
            return '\n'.join(f'✅ {ans}' for ans in exact_matches)
        self.suggestions = self._match_similar(query)
        if not self.suggestions:
            return '🤷\u200d♂️ Không tìm thấy câu trả lời phù hợp'
        suggestions_text = '\n'.join(
            f"{i + 1}. {line.split('||')[0].strip()}" for i, line in
            enumerate(self.suggestions))
        return f"""🤔 Không tìm thấy khớp tuyệt đối. Các gợi ý:
{suggestions_text}
👉 Chọn số thứ tự để xem câu trả lời"""

    def get_answer_by_index(self, index: int) ->str:
        if not 1 <= index <= len(self.suggestions):
            return '❌ Số thứ tự không hợp lệ'
        return f"💡 {self.suggestions[index - 1].split('||')[1].strip()}"


class KnowledgeHandler:

    def __init__(self):
        self.km = KnowledgeManager()
        self.awaiting_choice = False

    def can_handle(self, command: str) ->bool:
        return command.startswith(('ho:', 'thêm:', 'xem:', 'sửa:', 'xóa:',
            'xóa_chọn:'))

    def handle(self, command: str) ->bool:
        cmd = command.lower().strip()
        if self.awaiting_choice and cmd.isdigit():
            result = self.km.get_answer_by_index(int(cmd))
            self.awaiting_choice = False
            #print(result)
            #return True
            return result 
        if cmd.startswith(('thêm:', 'xem:', 'sửa:', 'xóa:', 'xóa_chọn:')):
            if cmd.startswith('thêm:'):
                result = self.km.add(cmd[5:])
            elif cmd == 'xem:':
                result = self.km.read()
            elif cmd.startswith('sửa:'):
                parts = cmd[4:].split(':', 1)
                if len(parts) == 2:
                    try:
                        line_num = int(parts[0].strip())
                        result = self.km.update(line_num, parts[1].strip())
                    except ValueError:
                        result = '❌ Số dòng phải là số nguyên'
                else:
                    result = '❌ Cú pháp: sửa:<số dòng>:<nội dung mới>'
            elif cmd.startswith('xóa:'):
                result = self.km.delete_by_keyword(cmd[4:])
            elif cmd.startswith('xóa_chọn:'):
                try:
                    num = int(cmd[9:].strip())
                    result = self.km.delete_by_index(num)
                except ValueError:
                    result = '❌ Số thứ tự phải là số nguyên'
            else:
                result = '🤷\u200d♂️ Không hiểu yêu cầu CRUD'
            #print(result)
            #return True
            return result 
        if cmd.startswith('ho:'):
            query = command[4:].strip()
            result = self.km.get_answer(query)
            if '👉 Chọn số thứ tự' in result:
                self.awaiting_choice = True
            #print(result)
            #return True
            return result 
        return False


plugin_info = {'enabled': True, 'command_handle': ['ho:', 'thêm:', 'xem',
    'sửa:', 'xóa:', 'xóa_chọn:'], 'register': lambda assistant: assistant.
    handlers.append(KnowledgeHandler())}
