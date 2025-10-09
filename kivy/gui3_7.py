# màn hình chat lúc chưa có nội dung là màu xám thay vì màu đen
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from threading import Thread
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
from kivy.animation import Animation
from kivy.graphics import Color, Rectangle
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
import os

from assistant import VirtualAssistant


# ================== Các màn hình ==================
class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout()
        layout.add_widget(Button(text="📌 Đây là Trang chủ"))
        self.add_widget(layout)


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout()
        layout.add_widget(Button(text="⚙️ Đây là Cài đặt"))
        self.add_widget(layout)


class InfoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout()
        layout.add_widget(Button(text="ℹ️ Đây là Thông tin"))
        self.add_widget(layout)


class NoteScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # 👉 ScrollView bao quanh TextInput
        scroll = ScrollView(size_hint=(1, 1))

        self.note_box = TextInput(
            hint_text="✍️ Viết ghi chú tại đây...",
            multiline=True,
            input_type="text",
            size_hint_y=None
        )
        self.note_box.bind(minimum_height=self.note_box.setter("height"))

        scroll.add_widget(self.note_box)
        layout.add_widget(scroll)

        # Nút lưu & xóa
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)

        save_btn = Button(text="Lưu")
        save_btn.bind(on_release=self.save_note)

        clear_btn = Button(text="Xóa")
        clear_btn.bind(on_release=lambda x: setattr(self.note_box, "text", ""))

        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(clear_btn)

        layout.add_widget(btn_layout)
        self.add_widget(layout)

    def on_pre_enter(self, *args):
        """Khi mở màn hình Note → chuyển chế độ resize + load file"""
        Window.softinput_mode = "resize"

        if os.path.exists("notes.txt"):
            with open("notes.txt", "r", encoding="utf-8") as f:
                self.note_box.text = f.read()

    def save_note(self, _):
        with open("notes.txt", "w", encoding="utf-8") as f:
            f.write(self.note_box.text)
        print("✅ Đã lưu ghi chú vào notes.txt")


class ChatScreen(Screen):
    def __init__(self, assistant, **kwargs):
        super().__init__(**kwargs)
        self.assistant = assistant

        # --- Nền xám nhạt ---
        with self.canvas.before:
            Color(0.5, 0.5, 0.5, 1)  # màu xám nhạt
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=lambda *x: setattr(self.bg_rect, 'size', self.size))
        self.bind(pos=lambda *x: setattr(self.bg_rect, 'pos', self.pos))

        # layout chính của Chat
        main_layout = BoxLayout(orientation="vertical", padding=5, spacing=5)

        # Vùng chat (scroll)
        self.chat_area = BoxLayout(orientation="vertical", size_hint_y=None, spacing=5)
        self.chat_area.bind(minimum_height=self.chat_area.setter("height"))

        scroll = ScrollView()
        scroll.add_widget(self.chat_area)
        main_layout.add_widget(scroll)

        # Vùng nhập + nút gửi
        input_layout = BoxLayout(size_hint_y=None, height=50, spacing=5)

        self.input_box = TextInput(
            hint_text="Nhập lệnh...",
            multiline=True,
            input_type="text",
            size_hint_y=None,
            height=50,
            padding=(10, 10),
            background_color=(1,1,1,1),  # nền trắng cho input
            foreground_color=(0,0,0,1),
            background_normal='',
            background_active=''
        )

        def adjust_input_height(instance, value):
            instance.height = max(50, instance.minimum_height)
            input_layout.height = instance.height

        self.input_box.bind(minimum_height=adjust_input_height)

        send_btn = Button(text="Gửi", size_hint_x=None, width=80)
        send_btn.bind(on_release=self.send_command)

        input_layout.add_widget(self.input_box)
        input_layout.add_widget(send_btn)

        main_layout.add_widget(input_layout)
        self.add_widget(main_layout)
    def on_pre_enter(self, *args):
        Window.softinput_mode = "pan"

    # Hiển thị tin nhắn
    def display_message(self, sender, message):
        if sender == "Bạn":
            bg_color = (0.1, 0.3, 0.6, 1)
            text_color = (1, 1, 1, 1)
        else:
            bg_color = (0.9, 0.9, 0.9, 1)
            text_color = (0, 0, 0, 1)

        txt = TextInput(
            text=f"{sender}: {message}",
            size_hint_y=None,
            readonly=True,
            background_color=bg_color,
            foreground_color=text_color,
            cursor_blink=False,
            background_normal='',
            background_active='',
            padding=(10, 10),
            multiline=True
        )

        def adjust_height(instance, value):
            instance.height = instance.minimum_height

        txt.bind(minimum_height=adjust_height)

        def on_double_tap(instance, touch):
            if instance.collide_point(*touch.pos) and touch.is_double_tap:
                Clipboard.copy(instance.text)
                print("📋 Copied:", instance.text)

        txt.bind(on_touch_down=on_double_tap)

        self.chat_area.add_widget(txt)

    # Gửi lệnh
    def send_command(self, _=None):
        command = self.input_box.text.strip()
        if not command:
            return

        self.display_message("Bạn", command)
        self.input_box.text = ""

        def process():
            response = self.assistant.process_command(command)
            if response:
                Clock.schedule_once(lambda dt: self.display_message("Asi-1", response))
            if response == "👋 Tạm biệt!":
                Clock.schedule_once(lambda dt: App.get_running_app().stop())

        Thread(target=process, daemon=True).start()

# ================== Giao diện chính ==================
class ChatUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="horizontal", **kwargs)

        # Khởi tạo trợ lý
        self.assistant = VirtualAssistant()
        self.assistant.loader.load_plugins(self.assistant)

        # --- Sidebar ---
        self.sidebar = BoxLayout(orientation='vertical', size_hint_x=None, width=0, opacity=0)

        btn_home = Button(text="Trang chủ")
        btn_home.bind(on_release=lambda x: self.switch_screen("home"))

        btn_chat = Button(text="Chat")
        btn_chat.bind(on_release=lambda x: self.switch_screen("chat"))

        btn_note = Button(text="Ghi chú")
        btn_note.bind(on_release=lambda x: self.switch_screen("note"))

        btn_settings = Button(text="Cài đặt")
        btn_settings.bind(on_release=lambda x: self.switch_screen("settings"))

        btn_info = Button(text="Thông tin")
        btn_info.bind(on_release=lambda x: self.switch_screen("info"))

        self.sidebar.add_widget(btn_home)
        self.sidebar.add_widget(btn_chat)
        self.sidebar.add_widget(btn_note)
        self.sidebar.add_widget(btn_settings)
        self.sidebar.add_widget(btn_info)
        self.add_widget(self.sidebar)

        # Vẽ nền trong suốt cho sidebar
        with self.sidebar.canvas.before:
            self.sidebar_color = Color(0, 0, 0, 0)
            self.sidebar_rect = Rectangle(size=self.sidebar.size, pos=self.sidebar.pos)

        self.sidebar.bind(size=lambda *x: setattr(self.sidebar_rect, 'size', self.sidebar.size))
        self.sidebar.bind(pos=lambda *x: setattr(self.sidebar_rect, 'pos', self.sidebar.pos))

        # --- Main layout ---
        main_layout = BoxLayout(orientation='vertical')
        self.add_widget(main_layout)

        # --- Top menu ngang ---
        top_menu = BoxLayout(size_hint_y=None, height=40)

        # Nút ☰ trong top menu
        self.hamburger_btn = Button(text="=", size_hint_x=None, width=50)
        self.hamburger_btn.bind(on_release=self.toggle_sidebar)
        top_menu.add_widget(self.hamburger_btn)

        # Các nút khác trong menu
        btn_home_top = Button(text="Trang chủ")
        btn_home_top.bind(on_release=lambda x: self.switch_screen("home"))
        top_menu.add_widget(btn_home_top)

        btn_chat_top = Button(text="Chat")
        btn_chat_top.bind(on_release=lambda x: self.switch_screen("chat"))
        top_menu.add_widget(btn_chat_top)

        btn_note_top = Button(text="Ghi chú")
        btn_note_top.bind(on_release=lambda x: self.switch_screen("note"))
        top_menu.add_widget(btn_note_top)

        btn_settings_top = Button(text="Cài đặt")
        btn_settings_top.bind(on_release=lambda x: self.switch_screen("settings"))
        top_menu.add_widget(btn_settings_top)

        btn_info_top = Button(text="Thông tin")
        btn_info_top.bind(on_release=lambda x: self.switch_screen("info"))
        top_menu.add_widget(btn_info_top)

        main_layout.add_widget(top_menu)

        # --- ScreenManager với hiệu ứng trượt ---
        self.sm = ScreenManager(transition=SlideTransition())
        self.sm.add_widget(ChatScreen(self.assistant, name="chat"))
        self.sm.add_widget(HomeScreen(name="home"))
        self.sm.add_widget(NoteScreen(name="note"))
        self.sm.add_widget(SettingsScreen(name="settings"))
        self.sm.add_widget(InfoScreen(name="info"))

        # 👉 Đặt mặc định là Chat
        self.sm.current = "chat"

        main_layout.add_widget(self.sm)

        # Thứ tự màn hình để xác định hướng slide
        self.screen_order = ["chat", "home", "note", "settings", "info"]

    def toggle_sidebar(self, instance):
        if self.sidebar.width == 0:
            self.sidebar.opacity = 1
            Animation(width=200, duration=0.3).start(self.sidebar)
        else:
            anim = Animation(width=0, opacity=0, duration=0.3)
            anim.start(self.sidebar)

    def switch_screen(self, screen_name):
        # Tự động chọn hướng trượt
        current_index = self.screen_order.index(self.sm.current)
        target_index = self.screen_order.index(screen_name)

        if target_index > current_index:
            self.sm.transition.direction = "left"
        else:
            self.sm.transition.direction = "right"

        self.sm.current = screen_name

        # Ẩn sidebar khi chọn xong
        if self.sidebar.width > 0:
            Animation(width=0, opacity=0, duration=0.3).start(self.sidebar)


class AssistantApp(App):
    def build(self):
        Window.softinput_mode = "resize"
        return ChatUI()


if __name__ == "__main__":
    AssistantApp().run()