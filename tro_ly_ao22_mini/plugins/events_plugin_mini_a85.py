# in ra tên đầy đủ của sự kiện để tránh nhầm lẫn 
import os
import json

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from typing import List, Dict, Optional


class EventHandler:

    def __init__(self, data_file='events.json'):
        self.data_file = data_file
        self.events: List[Dict] = []

        self.load_events()

    # =========================
    # LOAD / SAVE
    # =========================

    def load_events(self):

        if os.path.exists(self.data_file):

            try:
                with open(
                    self.data_file,
                    'r',
                    encoding='utf-8'
                ) as f:

                    self.events = json.load(f)

            except:
                self.events = []

    def save_events(self):

        with open(
            self.data_file,
            'w',
            encoding='utf-8'
        ) as f:

            json.dump(
                self.events,
                f,
                ensure_ascii=False,
                indent=2
            )

    # =========================
    # DATE PARSER
    # =========================

    def parse_date(self, text: str) -> datetime:

        text = text.strip().lower()

        if text == "hôm nay":
            return datetime.now()

        if text == "mai":
            return datetime.now() + timedelta(days=1)

        if text == "hôm qua":
            return datetime.now() - timedelta(days=1)

        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
        ]

        for fmt in formats:

            try:
                return datetime.strptime(text, fmt)

            except:
                pass

        raise ValueError(
            "Định dạng ngày không hợp lệ"
        )

    # =========================
    # ADD EVENT
    # =========================

    def add_event(
        self,
        content: str,
        date_text: Optional[str] = None
    ):

        if date_text:
            event_date = self.parse_date(date_text)
        else:
            event_date = datetime.now()

        event = {
            'content': content,
            'date': event_date.isoformat()
        }

        self.events.append(event)

        self.save_events()

        return event

    # =========================
    # FIND EVENT
    # =========================

    def find_event(
        self,
        keyword: str
    ) -> Optional[Dict]:

        for event in reversed(self.events):

            if keyword.lower() in (
                event['content'].lower()
            ):
                return event

        return None

    # =========================
    # FORMAT RELATIVE TIME
    # =========================

    def format_relative_time(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> str:

        diff = relativedelta(
            end_date,
            start_date
        )

        total_days = (
            end_date.date() -
            start_date.date()
        ).days

        parts = []

        if diff.years:
            parts.append(
                f"{diff.years} năm"
            )

        if diff.months:
            parts.append(
                f"{diff.months} tháng"
            )

        if diff.days:
            parts.append(
                f"{diff.days} ngày"
            )

        if not parts:
            parts.append("0 ngày")

        readable = " ".join(parts)

        return (
            f"{readable} "
            f"({total_days} ngày)"
        )

    # =========================
    # DAYS SINCE EVENT
    # =========================

    def time_since_event(
        self,
        keyword: str
    ) -> Optional[Dict]:

        event = self.find_event(keyword)

        if not event:
            return None

        event_date = datetime.fromisoformat(
            event['date']
        )

        now = datetime.now()

        return {
            "event": event,

            "time": self.format_relative_time(
                event_date,
                now
            )
        }

    # =========================
    # DAYS UNTIL EVENT
    # =========================

    def time_until_event(
        self,
        keyword: str
    ) -> Optional[Dict]:

        event = self.find_event(keyword)

        if not event:
            return None

        event_date = datetime.fromisoformat(
            event['date']
        )

        now = datetime.now()

        if event_date < now:
            return None

        return {
            "event": event,

            "time": self.format_relative_time(
                now,
                event_date
            )
        }

    # =========================
    # LIST EVENTS
    # =========================

    def list_events(self):

        if not self.events:

            print(
                "📭 Chưa có sự kiện nào"
            )

            return

        print(
            "\n📅 DANH SÁCH SỰ KIỆN\n"
        )

        for i, event in enumerate(
            self.events,
            start=1
        ):

            date_str = (
                datetime.fromisoformat(
                    event['date']
                ).strftime("%d/%m/%Y")
            )

            print(
                f"{i}. "
                f"{event['content']} "
                f"({date_str})"
            )


class EventCommandHandler:

    def __init__(
        self,
        event_handler: EventHandler
    ):

        self.event_handler = event_handler

        self.event_prefix = 'sự kiện:'

        self.question_prefixes = [
            'bao lâu rồi',
            'bao nhiêu ngày rồi',
            'mấy ngày rồi'
        ]

        self.future_prefixes = [
            'còn bao nhiêu ngày',
            'còn mấy ngày'
        ]

    # =========================
    # CAN HANDLE
    # =========================

    def can_handle(
        self,
        command: str
    ) -> bool:

        command_lower = command.lower()

        return (
            command_lower.startswith(
                self.event_prefix
            )

            or any(
                command_lower.endswith(q)
                for q in self.question_prefixes
            )

            or any(
                command_lower.endswith(q)
                for q in self.future_prefixes
            )

            or command_lower == (
                "danh sách sự kiện"
            )
        )

    # =========================
    # HANDLE
    # =========================

    def handle(
        self,
        command: str
    ) -> bool:

        command_lower = command.lower()

        # =====================
        # ADD EVENT
        # =====================

        if command_lower.startswith(
            self.event_prefix
        ):

            raw = command[
                len(self.event_prefix):
            ].strip()

            if not raw:

                print(
                    "⚠️ Vui lòng nhập sự kiện"
                )

                return True

            if "|" in raw:

                content, date_text = (
                    raw.split("|", 1)
                )

                content = content.strip()

                date_text = (
                    date_text.strip()
                )

                try:

                    self.event_handler.add_event(
                        content,
                        date_text
                    )

                    print(
                        f"📝 Đã ghi sự kiện: "
                        f"{content} "
                        f"({date_text})"
                    )

                except Exception as e:

                    print(
                        f"⚠️ Lỗi ngày tháng: "
                        f"{e}"
                    )

            else:

                self.event_handler.add_event(
                    raw
                )

                print(
                    f"📝 Đã ghi sự kiện: "
                    f"{raw}"
                )

            return True

        # =====================
        # LIST EVENTS
        # =====================

        if command_lower == (
            "danh sách sự kiện"
        ):

            self.event_handler.list_events()

            return True

        # =====================
        # FUTURE EVENT
        # =====================

        for q in self.future_prefixes:

            if command_lower.endswith(q):

                keyword = command[
                    :-len(q)
                ].strip()

                result = (
                    self.event_handler
                    .time_until_event(
                        keyword
                    )
                )

                if result is None:

                    print(
                        f"🔍 Không tìm thấy "
                        f"hoặc sự kiện đã qua: "
                        f"'{keyword}'"
                    )

                else:

                    print(
                        f"📅 "
                        f"'{result['event']['content']}' "
                        f"còn "
                        f"{result['time']}"
                    )

                return True

        # =====================
        # PAST EVENT
        # =====================

        keyword = command

        for q in self.question_prefixes:

            if command_lower.endswith(q):

                keyword = keyword[
                    :-len(q)
                ].strip()

                break

        if not keyword:

            print(
                "⚠️ Vui lòng nhập từ khóa"
            )

            return True

        result = (
            self.event_handler
            .time_since_event(
                keyword
            )
        )

        if result is None:

            print(
                f"🔍 Không tìm thấy "
                f"'{keyword}'"
            )

        else:

            print(
                f"⏳ "
                f"'{result['event']['content']}' "
                f"đã xảy ra "
                f"{result['time']} trước"
            )

        return True


# =========================
# PLUGIN
# =========================

event_handler = EventHandler()

plugin_info = {
    'enabled': True,

    'register': (
        lambda core:
        core.handlers.append(
            EventCommandHandler(
                event_handler
            )
        )
    ),

    'command_handle': [
        'sự kiện: mưa',
        'sự kiện: sinh nhật | 2026-04-20',
        'sự kiện: trời mưa | hôm qua',
        'danh sách sự kiện',
        'sự kiện: đi du lịch | 2026-06-01'
    ],
}