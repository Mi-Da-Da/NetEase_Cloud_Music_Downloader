import requests
import re
import os
from core.encrypt import get_music_url

MUSIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "music")

def get_default_music_dir():
    return MUSIC_DIR

def set_music_dir(path):
    global MUSIC_DIR
    MUSIC_DIR = path
    os.makedirs(MUSIC_DIR, exist_ok=True)

def save(title, music_url):
    new_title = re.sub(r'[\\/:*?"<>|]', '', title)
    response = requests.get(music_url, stream=True, timeout=30)
    file_path = os.path.join(MUSIC_DIR, f"{new_title}.mp3")
    with open(file_path, "wb") as f:
        for chunk in response.iter_content(8192):
            if chunk:
                f.write(chunk)

def is_song_exist(title):
    new_title = re.sub(r'[\\/:*?"<>|]', '', title)
    file_path = os.path.join(MUSIC_DIR, f"{new_title}.mp3")
    return os.path.exists(file_path)

# 下载歌曲
def download_song(cookie_str, csrf_token, js_ctx, song):
    music_id = song["id"]
    title = song["title"]
    try:
        # 检查歌曲是否已存在
        if is_song_exist(title):
            return {
                "success": True,
                "title": title,
                "skipped": True
            }
        # 获取下载链接
        music_url = get_music_url(cookie_str, csrf_token, js_ctx, music_id)
        if not music_url:
            return {
                "success": False,
                "title": title,
                "skipped": False
            }
        # 保存歌曲
        save(title, music_url)
        # 返回状态
        return {
            "success": True,
            "title": title,
            "skipped": False
        }
    except Exception as e:
        print(f"\n下载失败: {title}")
        print(e)
        return {
            "success": False,
            "title": title,
            "skipped": False
        }