# nhiều kênh
import feedparser
import webbrowser
import threading
import time
import os
import json
from typing import Any, Dict, List

# ==================== CẤU HÌNH ====================
CHANNEL_IDS = [
    # Tú ATS
    "UCu3q59AXNNDGxT9LUBQeELA", 
    
    # Thái Phạm
     "UCDJIGO_3ycJAKLPv7Yh396A", 
    
    # QTstocks
    "UCLWrocDxNVocoPs5d_qCaOg",
    
    # Nhật Quang Chứng khoán
    "UCZQdpU9kfmwzYuKJWrb_1Hw",
    
    # w5n
    "UCkgjUHB8sdWbmdp39swMrTg"
]
CHECK_INTERVAL = 30                    # giây (kiểm tra tất cả kênh mỗi 30s)
DATA_FILE = os.path.join(os.path.dirname(__file__), "youtube_monitor_data.json")
# ==================================================

_last_video_ids: Dict[str, str] = {}   # channel_id -> last_video_id
_assistant_ref = None

def load_last_videos():
    """Đọc dữ liệu đã lưu (dict: channel_id -> last_video_id)"""
    global _last_video_ids
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                _last_video_ids = data.get('last_video_ids', {})
        except:
            pass

def save_last_videos():
    """Lưu dict last_video_ids vào file"""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump({'last_video_ids': _last_video_ids}, f)
    except:
        pass

def get_latest_video_from_channel(channel_id: str):
    """Lấy video mới nhất từ RSS của một kênh"""
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        feed = feedparser.parse(rss_url)
        if feed.entries:
            entry = feed.entries[0]
            video_id = entry.get('yt_videoid')
            if not video_id:
                link = entry.link
                if '?v=' in link:
                    video_id = link.split('?v=')[-1].split('&')[0]
            title = entry.title
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            return video_id, title, video_url
    except Exception as e:
        print(f"[YouTubeMonitor][{channel_id}] Lỗi RSS: {e}")
    return None, None, None

def monitor_loop():
    global _assistant_ref, _last_video_ids
    load_last_videos()
    print(f"[YouTubeMonitor] Đang theo dõi {len(CHANNEL_IDS)} kênh, kiểm tra mỗi {CHECK_INTERVAL}s")
    
    while True:
        for ch_id in CHANNEL_IDS:
            try:
                video_id, title, url = get_latest_video_from_channel(ch_id)
                if not video_id:
                    continue
                
                last_id = _last_video_ids.get(ch_id)
                if last_id != video_id:
                    print(f"[YouTubeMonitor] 🎬 Kênh {ch_id} có video mới: {title}")
                    webbrowser.open(url)          # Tự động mở trình duyệt
                    _last_video_ids[ch_id] = video_id
                    save_last_videos()
                    if _assistant_ref:
                        print(f"[YouTubeMonitor] Đã mở video: {title}")
            except Exception as e:
                print(f"[YouTubeMonitor][{ch_id}] Lỗi: {e}")
        
        time.sleep(CHECK_INTERVAL)

def register(assistant: Any):
    global _assistant_ref
    _assistant_ref = assistant
    thread = threading.Thread(target=monitor_loop, daemon=True)
    thread.start()
    print("[YouTubeMonitor] Plugin đa kênh đã được kích hoạt và chạy ngầm.")

plugin_info = {
    "enabled": True,
    "register": register,
    "command_handle": None
}