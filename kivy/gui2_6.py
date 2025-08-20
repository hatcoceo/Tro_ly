from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from threading import Thread
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label

from assistant import VirtualAssistant  # import từ file assistant.py


# ========================
# Chat giao diện cũ
# ========================
class ChatUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)

        # Khởi tạo trợ lý
        self.assistant = VirtualAssistant()
        self.assistant.loader.load_plugins(self.assistant)

        # Vùng chat (scroll)
        self.chat_area = BoxLayout(orientation="vertical", size_hint_y=None)
        self.chat_area.bind(minimum_height=self.chat_area.setter("height"))

        scroll = ScrollView()
        scroll.add_widget(self.chat_area)
        self.add_widget(scroll)

        # Vùng nhập + nút gửi
        input_layout = BoxLayout(size_hint_y=None, height=50)

        self.input_box = TextInput(
            hint_text="Nhập lệnh...",
            multiline=True,
            input_type="text",
            size_hint_y=None,
            height=50,
            padding=(10, 10)
        )

        # ✅ Tự động giãn chiều cao khi nhập nhiều dòng
        def adjust_input_height(instance, value):
            instance.height = max(50, instance.minimum_height)
            input_layout.height = instance.height

        self.input_box.bind(minimum_height=adjust_input_height)

        send_btn = Button(text="Gửi", size_hint_x=None, width=80)
        send_btn.bind(on_release=self.send_command)

        input_layout.add_widget(self.input_box)
        input_layout.add_widget(send_btn)

        self.add_widget(input_layout)

        # ✅ Nút chuyển sang màn hình khác
        nav_btn = Button(text="👉 Sang màn hình khác", size_hint_y=None, height=50)
        nav_btn.bind(on_release=lambda x: setattr(self.parent.manager, "current", "other"))
        self.add_widget(nav_btn)

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


# ========================
# Các màn hình
# ========================
class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(ChatUI())


class OtherScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical")
        layout.add_widget(Label(text="Đây là màn hình khác 🎉"))

        back_btn = Button(text="⬅️ Quay lại Chat", size_hint_y=None, height=50)
        back_btn.bind(on_release=lambda x: setattr(self.manager, "current", "chat"))
        layout.add_widget(back_btn)

        self.add_widget(layout)


# ========================
# App chính
# ========================
class AssistantApp(App):
    def build(self):
        Window.softinput_mode = "pan"

        sm = ScreenManager()
        sm.add_widget(ChatScreen(name="chat"))
        sm.add_widget(OtherScreen(name="other"))
        return sm


if __name__ == "__main__":
    AssistantApp().run()