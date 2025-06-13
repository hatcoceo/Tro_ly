# viet ma theo kien truc oop tot hơn( interface - abstract class)
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional
import datetime
import difflib
import re
from translate import Translator
from lunarcalendar import Converter, Solar
import os
import shutil

# ==================== INTERFACES ====================
class IKnowledgeManager(ABC):
    """Interface cho quản lý tri thức"""
    @abstractmethod
    def add_knowledge(self, question: str, answer: str) -> None:
        pass
    
    @abstractmethod
    def get_answer(self, question: str) -> List[str]:
        pass
    
    @abstractmethod
    def search(self, keyword: str) -> List[Tuple[str, str]]:
        pass
    
    @abstractmethod
    def delete(self, question: str) -> bool:
        pass
    
    @abstractmethod
    def update(self, question: str, new_answer: str) -> bool:
        pass
    
    @abstractmethod
    def generate_document(self, topic: str) -> str:
        pass

class IEventManager(ABC):
    """Interface cho quản lý sự kiện"""
    @abstractmethod
    def add_event(self, event: str) -> None:
        pass
    
    @abstractmethod
    def list_events(self) -> List[str]:
        pass
    
    @abstractmethod
    def get_events_since(self, days: int) -> List[Tuple[str, int]]:
        pass
    
    @abstractmethod
    def handle_duration_question(self, question: str) -> bool:
        pass
    
    @abstractmethod
    def add_advanced_event(self, question: str) -> bool:
        pass

class ICommandHandler(ABC):
    """Interface cho xử lý lệnh"""
    @abstractmethod
    def can_handle(self, command: str) -> bool:
        pass
    
    @abstractmethod
    def handle(self, command: str) -> bool:
        pass

# ==================== ABSTRACT CLASSES ====================
class BaseFileManager(ABC):
    """Abstract class cho quản lý file"""
    @staticmethod
    def append_to_file(file_path: str, content: str) -> None:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(content + "\n")
    
    @staticmethod
    def read_file(file_path: str) -> List[str]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return []
    
    @staticmethod
    def overwrite_file(file_path: str, lines: List[str]) -> None:
        with open(file_path, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")

class BaseKnowledgeManager(IKnowledgeManager, BaseFileManager):
    """Abstract class triển khai quản lý tri thức"""
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.knowledge: Dict[str, List[str]] = {}
        self.load_knowledge()
    
    def load_knowledge(self) -> None:
        """Tải tri thức từ storage"""
        for line in self.read_file(self.storage_path):
            if "||" in line:
                question, answer = line.split("||", 1)
                self.knowledge.setdefault(question.strip().lower(), []).append(answer.strip())
    
    def save_knowledge(self) -> None:
        """Lưu tri thức vào storage"""
        lines = [f"{q}||{a}" for q, answers in self.knowledge.items() for a in answers]
        self.overwrite_file(self.storage_path, lines)
    
    def add_knowledge(self, question: str, answer: str) -> None:
        question = question.lower().strip()
        self.knowledge.setdefault(question, []).append(answer.strip())
        self.save_knowledge()
    
    def get_answer(self, question: str) -> List[str]:
        return self.knowledge.get(question.lower().strip(), [])
    
    def search(self, keyword: str) -> List[Tuple[str, str]]:
        keyword = keyword.lower()
        return [(q, a) for q, answers in self.knowledge.items() 
                if keyword in q for a in answers]
    
    def delete(self, question: str) -> bool:
        question = question.lower().strip()
        if question in self.knowledge:
            del self.knowledge[question]
            self.save_knowledge()
            return True
        return False
    
    def update(self, question: str, new_answer: str) -> bool:
        question = question.lower().strip()
        if question in self.knowledge:
            self.knowledge[question] = [new_answer.strip()]
            self.save_knowledge()
            return True
        return False
    
    def generate_document(self, topic: str) -> str:
        results = self.search(topic)
        if not results:
            return f"Tôi chưa có đủ thông tin về '{topic}'."
        
        document = f"Thông tin về {topic}:\n"
        for i, (_, answer) in enumerate(results, 1):
            document += f"{i}. {answer}\n"
        
        document += "\nThông tin liên quan:\n"
        for question, _ in results:
            document += f"- {question}\n"
        
        return document

class BaseEventManager(IEventManager, BaseFileManager):
    """Abstract class triển khai quản lý sự kiện"""
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.events: List[Tuple[datetime.datetime, str]] = []
        self.load_events()
    
    def load_events(self) -> None:
        """Tải sự kiện từ storage"""
        for line in self.read_file(self.storage_path):
            if "||" in line:
                time_str, event = line.split("||", 1)
                try:
                    time = datetime.datetime.strptime(time_str.strip(), "%Y-%m-%d %H:%M:%S")
                    self.events.append((time, event.strip()))
                except ValueError:
                    continue
    
    def save_events(self) -> None:
        """Lưu sự kiện vào storage"""
        lines = [f"{time.strftime('%Y-%m-%d %H:%M:%S')}||{event}" 
                for time, event in self.events]
        self.overwrite_file(self.storage_path, lines)
    
    def add_event(self, event: str) -> None:
        time = datetime.datetime.now()
        self.events.append((time, event.strip()))
        self.save_events()
    
    def list_events(self) -> List[str]:
        return [f"{time.strftime('%Y-%m-%d %H:%M')} - {event}" 
                for time, event in self.events]
    
    def get_events_since(self, days: int) -> List[Tuple[str, int]]:
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        return [(event, (datetime.datetime.now() - time).days)
               for time, event in self.events if time >= cutoff]
    
    def handle_duration_question(self, question: str) -> bool:
        keyword = question.replace("diễn ra bao lâu", "").replace("bao lâu rồi", "").strip(" ?")
        found = False
        
        for time, event in self.events:
            if keyword.lower() in event.lower():
                days = (datetime.datetime.now() - time).days
                print(f"📆 Sự kiện '{event}' diễn ra vào {time.strftime('%Y-%m-%d')}, "
                     f"cách đây {days} ngày.")
                found = True
        
        if not found:
            print("🔎 Không tìm thấy sự kiện.")
        
        return found
    
    def add_advanced_event(self, question: str) -> bool:
        match = re.search(r"(\d+)\s*ngày\s*rồi", question.lower())
        if match:
            days = int(match.group(1))
            start_date = datetime.datetime.now() - datetime.timedelta(days=days)
            event = re.sub(r"đã|(\d+\s*ngày\s*rồi)", "", question, flags=re.I).strip()
            if not event:
                event = "Sự kiện"
            
            self.add_event(f"{event} - bắt đầu từ {start_date.strftime('%Y-%m-%d')}")
            print(f"📝 Đã ghi sự kiện nâng cao: '{event}'")
            return True
        return False

# ==================== CONCRETE COMMAND HANDLERS ====================
class TeachCommandHandler(ICommandHandler):
    def __init__(self, knowledge_manager: IKnowledgeManager):
        self.km = knowledge_manager
    
    def can_handle(self, command: str) -> bool:
        return command.startswith(("dạy:", "ghi nhớ:"))
    
    def handle(self, command: str) -> bool:
        try:
            _, content = command.split(":", 1)
            question, answer = content.split("||", 1)
            self.km.add_knowledge(question.strip(), answer.strip())
            print("✅ Đã ghi thêm tri thức mới")
            return True
        except ValueError:
            print("❗ Sai cú pháp. Dùng: dạy: câu hỏi || câu trả lời")
            return False

class DeleteCommandHandler(ICommandHandler):
    def __init__(self, knowledge_manager: IKnowledgeManager):
        self.km = knowledge_manager
    
    def can_handle(self, command: str) -> bool:
        return command.startswith("xóa:")
    
    def handle(self, command: str) -> bool:
        question = command.split(":", 1)[1].strip()
        if self.km.delete(question):
            print(f"🗑️ Đã xóa: '{question}'")
        else:
            print(f"⚠️ Không tìm thấy: '{question}'")
        return True

class EventCommandHandler(ICommandHandler):
    def __init__(self, event_manager: IEventManager):
        self.em = event_manager
    
    def can_handle(self, command: str) -> bool:
        return command.startswith("sự kiện:")
    
    def handle(self, command: str) -> bool:
        event = command.split(":", 1)[1].strip()
        if event:
            self.em.add_event(event)
            print("📝 Đã ghi sự kiện")
        else:
            print("⚠️ Bạn chưa nhập sự kiện")
        return True

class SearchCommandHandler(ICommandHandler):
    def __init__(self, knowledge_manager: IKnowledgeManager):
        self.km = knowledge_manager
    
    def can_handle(self, command: str) -> bool:
        return command.startswith("tìm:")
    
    def handle(self, command: str) -> bool:
        keyword = command.split(":", 1)[1].strip()
        results = self.km.search(keyword)
        if results:
            print(f"🔍 Tìm thấy {len(results)} kết quả:")
            for i, (q, a) in enumerate(results, 1):
                print(f"{i}. {q} => {a}")
        else:
            print("❌ Không tìm thấy kết quả nào")
        return True

class DocumentCommandHandler(ICommandHandler):
    def __init__(self, knowledge_manager: IKnowledgeManager):
        self.km = knowledge_manager
    
    def can_handle(self, command: str) -> bool:
        return command.startswith("tạo văn bản:")
    
    def handle(self, command: str) -> bool:
        topic = command.split(":", 1)[1].strip()
        print(self.km.generate_document(topic))
        return True

class TranslateCommandHandler(ICommandHandler):
    def can_handle(self, command: str) -> bool:
        return command.startswith("dịch:")
    
    def handle(self, command: str) -> bool:
        try:
            _, text = command.split(":", 1)
            translator = Translator(to_lang="en", from_lang="vi")
            result = translator.translate(text.strip())
            print(f"🌐 Dịch: {result}")
            return True
        except Exception as e:
            print(f"❌ Lỗi khi dịch: {str(e)}")
            return True

class CalculationHandler(ICommandHandler):
    def can_handle(self, command: str) -> bool:
        return re.match(r"^[\d\s\+\-\*/\.\%\(\)]+$", command)
    
    def handle(self, command: str) -> bool:
        try:
            allowed_chars = "0123456789+-*/().% "
            if all(c in allowed_chars for c in command):
                result = eval(command)
                print(f"🧮 Kết quả: {result}")
            else:
                print("⚠️ Biểu thức chứa ký tự không hợp lệ")
            return True
        except:
            print("❌ Không thể tính toán. Biểu thức sai cú pháp")
            return True

class CalendarHandler(ICommandHandler):
    def can_handle(self, command: str) -> bool:
        return command in [
            "hôm nay là thứ mấy", 
            "hôm nay là ngày gì", 
            "nay thứ mấy", 
            "hôm nay ngày bao nhiêu"
        ]
    
    def handle(self, command: str) -> bool:
        today = datetime.datetime.now()
        weekday = ["Thứ Hai", "Thứ Ba", "Thứ Tư", 
                  "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"][today.weekday()]
        solar_date = today.strftime("%d/%m/%Y")
        
        solar = Solar(today.year, today.month, today.day)
        lunar = Converter.Solar2Lunar(solar)
        lunar_date = f"{lunar.day}/{lunar.month}/{lunar.year}"
        
        print(f"📅 Hôm nay là {weekday}, ngày {solar_date} (Dương lịch)")
        print(f"🌙 Lịch âm: {lunar_date}")
        return True

class DurationHandler(ICommandHandler):
    def __init__(self, event_manager: IEventManager):
        self.em = event_manager
    
    def can_handle(self, command: str) -> bool:
        return "bao lâu" in command
    
    def handle(self, command: str) -> bool:
        return self.em.handle_duration_question(command)

class AdvancedEventHandler(ICommandHandler):
    def __init__(self, event_manager: IEventManager):
        self.em = event_manager
    
    def can_handle(self, command: str) -> bool:
        return "ngày rồi" in command.lower()
    
    def handle(self, command: str) -> bool:
        return self.em.add_advanced_event(command)

class ListKnowledgeHandler(ICommandHandler):
    def __init__(self, knowledge_manager: IKnowledgeManager):
        self.km = knowledge_manager
    
    def can_handle(self, command: str) -> bool:
        return command == "xem tri thức"
    
    def handle(self, command: str) -> bool:
        if not self.km.knowledge:
            print("❌ Chưa có tri thức")
            return True
        
        print("📚 Danh sách tri thức:")
        for i, (q, answers) in enumerate(self.km.knowledge.items(), 1):
            print(f"{i}. {q}")
            for a in answers:
                print(f"   - {a}")
        return True

class ListEventHandler(ICommandHandler):
    def __init__(self, event_manager: IEventManager):
        self.em = event_manager
    
    def can_handle(self, command: str) -> bool:
        return command == "xem sự kiện"
    
    def handle(self, command: str) -> bool:
        events = self.em.list_events()
        if not events:
            print("📭 Không có sự kiện nào")
        else:
            print("📅 Danh sách sự kiện:")
            for event in events:
                print(f" - {event}")
        return True

class ExitHandler(ICommandHandler):
    def can_handle(self, command: str) -> bool:
        return command.lower() in ["thoát", "exit", "quit"]
    
    def handle(self, command: str) -> bool:
        print("👋 Hẹn gặp lại!")
        return False  # Dừng chương trình

# ==================== MAIN ASSISTANT CLASS ====================
class VirtualAssistant:
    def __init__(self):
        # Khởi tạo các manager
        self.km = BaseKnowledgeManager("tri_thuc.txt")
        self.em = BaseEventManager("su_kien.txt")
        
        # Khởi tạo các command handler
        self.handlers = [
            TeachCommandHandler(self.km),
            DeleteCommandHandler(self.km),
            EventCommandHandler(self.em),
            SearchCommandHandler(self.km),
            DocumentCommandHandler(self.km),
            TranslateCommandHandler(),
            CalculationHandler(),
            CalendarHandler(),
            DurationHandler(self.em),
            AdvancedEventHandler(self.em),
            ListKnowledgeHandler(self.km),
            ListEventHandler(self.em),
            ExitHandler()
        ]
    
    def process_input(self, user_input: str) -> bool:
        """Xử lý đầu vào từ người dùng và trả về False nếu muốn dừng chương trình"""
        user_input = user_input.strip()
        
        # Kiểm tra các handler có thể xử lý
        for handler in self.handlers:
            if handler.can_handle(user_input):
                return handler.handle(user_input)
        
        # Xử lý mặc định nếu không có handler nào nhận
        return self._handle_unknown_input(user_input)
    
    def _handle_unknown_input(self, user_input: str) -> bool:
        """Xử lý khi không có handler nào nhận đầu vào"""
        # Kiểm tra trong tri thức
        answers = self.km.get_answer(user_input)
        if answers:
            print("🧠 Tôi biết câu trả lời:")
            for ans in answers:
                print(f" - {ans}")
            return True
        
        # Gợi ý câu hỏi tương tự
        similar = difflib.get_close_matches(
            user_input, 
            self.km.knowledge.keys(), 
            n=3, 
            cutoff=0.6
        )
        
        if similar:
            print("❓ Có phải bạn muốn hỏi:")
            for i, q in enumerate(similar, 1):
                print(f" {i}. {q}")
            return True
        
        # Hỏi người dùng để học
        print("🤔 Tôi chưa biết câu trả lời.")
        answer = input("Bạn có thể dạy tôi không? (Nhập câu trả lời hoặc Enter để bỏ qua): ").strip()
        if answer:
            self.km.add_knowledge(user_input, answer)
            print("✅ Cảm ơn! Tôi đã học được điều mới.")
            return True
        
        print("🤷‍♂️ Tôi không hiểu yêu cầu của bạn.")
        return True

# ==================== MAIN FUNCTION ====================
def main():
    print("👋 Xin chào! Tôi là trợ lý ảo thông minh")
    print("Gõ 'thoát', 'exit' hoặc 'quit' để kết thúc")
    
    assistant = VirtualAssistant()
    
    while True:
        try:
            user_input = input("\n❓ Bạn muốn biết điều gì?: ").strip()
            if not user_input:
                continue
                
            if not assistant.process_input(user_input):
                break
                
        except KeyboardInterrupt:
            print("\n👋 Tạm biệt!")
            break
        except Exception as e:
            print(f"⚠️ Có lỗi xảy ra: {str(e)}")

if __name__ == "__main__":
    main()
