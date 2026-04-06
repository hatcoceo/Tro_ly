import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from urllib.parse import quote

# ====== RSS NGUỒN ======
RSS_FEEDS = {
    "vn": "https://vnexpress.net/rss/tin-moi-nhat.rss",
    "bbc": "http://feeds.bbci.co.uk/news/rss.xml",
    "cafebiz": "https://cafebiz.vn/rss/home.rss",
    "dantri": "https://dantri.com.vn/rss/home.rss",
    "gg": "google"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ====== GOOGLE RSS ======
def build_google_rss(keyword: str) -> str:
    query = quote(keyword)
    return f"https://news.google.com/rss/search?q={query}&hl=vi&gl=VN&ceid=VN:vi"


# ====== RESOLVE LINK GOOGLE (CHUẨN NHẤT) ======
def resolve_google_link(url: str) -> str:
    try:
        session = requests.Session()

        resp = session.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept-Language": "en-US,en;q=0.9",
            },
            allow_redirects=True,
            timeout=5
        )

        return resp.url

    except Exception:
        return url


def normalize_title(title: str) -> str:
    return title.strip().lower()


# ====== HANDLER ======
class NewsHandler:
    def __init__(self, assistant: Any):
        self.assistant = assistant

    def can_handle(self, command: str) -> bool:
        return command.startswith("tin") or command.startswith("news")

    def handle(self, command: str):
        parts = command.split()

        limit = 15
        source = None
        keywords = []

        # ===== PARSE COMMAND =====
        for p in parts[1:]:
            if p.isdigit():
                limit = int(p)
            elif p in RSS_FEEDS:
                source = p
            else:
                keywords.append(p.lower())

        keyword = " ".join(keywords) if keywords else None

        print("📰 Đang lấy tin tức...\n")

        articles = self.fetch_news(source, keyword)

        if not articles:
            print("❌ Không tìm thấy tin phù hợp")
            return

        for i, article in enumerate(articles[:limit], 1):
            print(f"{i}. {article['title']}")
            print(f"   🌐 {article['source']}")
            print(f"   🔗 {article['link']}\n")

    # ===== FETCH =====
    def fetch_news(self, source_filter=None, keyword=None) -> List[Dict]:
        articles = []
        seen_titles = set()

        feeds = RSS_FEEDS.items()

        if source_filter:
            feeds = [(source_filter, RSS_FEEDS[source_filter])]

        for source_name, url in feeds:
            try:
                # ===== GOOGLE RSS =====
                if source_name == "gg":
                    if not keyword:
                        continue
                    url = build_google_rss(keyword)

                response = requests.get(url, headers=HEADERS, timeout=5)

                if response.status_code != 200:
                    raise Exception("Bad response")

                root = ET.fromstring(response.content)

                for i, item in enumerate(root.findall(".//item")):
                    title = item.find("title")
                    link = item.find("link")

                    if title is None or link is None:
                        continue

                    title_text = title.text.strip()
                    norm_title = normalize_title(title_text)

                    # ===== LỌC TRÙNG =====
                    if not title_text or norm_title in seen_titles:
                        continue

                    link_text = link.text.strip()

                    # ===== GOOGLE FIX =====
                    if source_name == "gg":
                        # chỉ resolve top 5 để tránh chậm
                        if i < 5:
                            link_text = resolve_google_link(link_text)

                        source_tag = item.find("source")
                        real_source = source_tag.text if source_tag is not None else "GOOGLE"
                    else:
                        real_source = source_name.upper()

                    seen_titles.add(norm_title)

                    articles.append({
                        "title": title_text,
                        "link": link_text,
                        "source": real_source
                    })

            except Exception as e:
                print(f"⚠️ Lỗi RSS ({source_name}): {e}")

        return articles


# ===== REGISTER =====
def register(assistant):
    assistant.handlers.append(NewsHandler(assistant))


plugin_info = {
    "enabled": True,
    "register": register,
    "command_handle": ["tin", "news"]
}