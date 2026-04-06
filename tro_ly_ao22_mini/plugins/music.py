import webbrowser
import urllib.parse
import urllib.request
import re
import requests
from bs4 import BeautifulSoup

# ===================== YOUTUBE =====================
def get_first_video(query):
    try:
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
        html = urllib.request.urlopen(url).read().decode()
        video_ids = re.findall(r"watch\?v=(\S{11})", html)

        if video_ids:
            return "https://www.youtube.com/watch?v=" + video_ids[0]
    except:
        return None


# ===================== SEARCH (FIX LINK) =====================
def search_duck(query):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}

        url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
        res = requests.get(url, headers=headers, timeout=5)

        soup = BeautifulSoup(res.text, "html.parser")

        links = []

        for a in soup.find_all("a", class_="result__a"):
            href = a.get("href")

            if href and "uddg=" in href:
                # 👉 lấy link thật
                real_url = urllib.parse.parse_qs(
                    urllib.parse.urlparse(href).query
                ).get("uddg", [""])[0]

                real_url = urllib.parse.unquote(real_url)

                if real_url.startswith("http"):
                    links.append(real_url)

        return links[:3]

    except Exception as e:
        print("❌ Lỗi search:", e)
        return []


# ===================== GET CONTENT =====================
def get_page_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)

        soup = BeautifulSoup(res.text, "html.parser")

        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text() for p in paragraphs)

        return text[:3000]

    except:
        return ""


# ===================== SUMMARIZE =====================
def summarize(text):
    sentences = text.split(".")
    sentences = [s.strip() for s in sentences if len(s) > 20]

    if not sentences:
        return "⚠️ Không đủ dữ liệu."

    return ". ".join(sentences[:3]) + "."


# ===================== MAIN =====================
def search_and_answer(query):
    print("🔎 Query:", query)

    # thêm "là gì" để dễ tìm
    links = search_duck(query + " là gì")

    print("🔗 Links:", links)

    if not links:
        return "⚠️ Không tìm thấy kết quả."

    full_text = ""

    for link in links:
        content = get_page_content(link)
        full_text += content + "\n"

    if not full_text.strip():
        return "⚠️ Không đọc được nội dung web."

    return summarize(full_text)


# ===================== REGISTER =====================
def register(assistant):

    # 🎵 MUSIC
    class MusicHandler:
        def can_handle(self, command):
            return "nhạc" in command.lower()

        def handle(self, command):
            keyword = command.replace("mở nhạc", "").strip()

            if not keyword:
                webbrowser.open("https://youtube.com")
                print("🎵 Mở YouTube")
                return

            print("🎵 Tìm nhạc:", keyword)

            url = get_first_video(keyword)

            if url:
                webbrowser.open(url)
                print("🎧 Đang phát...")
            else:
                print("❌ Không tìm thấy nhạc")


    # 🌐 WEB SEARCH
    class WebHandler:
        def can_handle(self, command):
            keywords = ["là gì", "là ai", "ai là", "tại sao", "ở đâu"]
            return any(k in command.lower() for k in keywords)

        def handle(self, command):
            print("🌐 Đang tìm kiếm...")

            result = search_and_answer(command)

            print("🤖", result)


    assistant.handlers.append(MusicHandler())
    assistant.handlers.append(WebHandler())


# ===================== PLUGIN INFO =====================
plugin_info = {
    "enabled": True,
    "register": register
}