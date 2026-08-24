from core.login import init, login, get_cookies
from core.encrypt import get_js_code
from modules.playlist import get_playlist_titles, select_playlist
from modules.song import get_music_info
from modules.downloader import download_song, get_default_music_dir, set_music_dir
from modules.search import get_search_results
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote
import tkinter as tk
from tkinter import filedialog

# 多线程下载歌曲
def download_songs(cookie_str, csrf_token, js_ctx, songs):
    # 设置参数
    success_count = 0
    fail_count = 0
    skipped_count = 0
    max_workers = 8
    failed_songs = []
    # 下载一首歌曲
    if len(songs) == 1:
        result = download_song(cookie_str, csrf_token, js_ctx, songs[0])
        if result["success"]:
            if result.get("skipped", False):
                skipped_count += 1
            else:
                success_count += 1
        else:
            fail_count += 1
            failed_songs.append({"title": result["title"]})
    # 下载多首歌曲
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for song in songs:
                future = executor.submit(download_song, cookie_str, csrf_token, js_ctx, song)
                futures.append(future)
            # 进度条显示
            with tqdm(total=len(futures)) as pbar:
                for future in as_completed(futures):
                    result = future.result()
                    if result["success"]:
                        if result.get("skipped", False):
                            skipped_count += 1
                        else:
                            success_count += 1
                    else:
                        fail_count += 1
                        failed_songs.append({"title": result["title"]})
                    pbar.set_postfix({"成功": success_count, "失败": fail_count, "跳过": skipped_count})
                    pbar.update(1)

    print(f"歌曲总数: {len(songs)} 首")
    print(f"成功下载: {success_count} 首")
    print(f"已下载: {skipped_count} 首")
    print(f"下载失败: {fail_count} 首")
    if failed_songs:
        print("❌ 以下歌曲下载失败：")
        for i, song in enumerate(failed_songs, 1):
            print(f"{i}. {song['title']}")
    else:
        print("✅ 所有歌曲下载成功")

# 解析选择
def parse_selections(input_str, max_index):
    indices = set()
    parts = input_str.split(',')
    for part in parts:
        part = part.strip()
        # 序号范围中的歌曲
        if '-' in part:
            try:
                start, end = part.split('-')
                start_idx = int(start.strip())
                end_idx = int(end.strip())
                for idx in range(min(start_idx, end_idx), max(start_idx, end_idx) + 1):
                    if 1 <= idx <= max_index:
                        indices.add(idx)
            except ValueError:
                continue
        # 单独序号的歌曲
        else:
            try:
                idx = int(part)
                if 1 <= idx <= max_index:
                    indices.add(idx)
            except ValueError:
                continue
    return sorted(list(indices))

# 选择保存目录
def choose_save_directory():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    root.update()

    default_dir = get_default_music_dir()
    selected_dir = filedialog.askdirectory(
        title="选择歌曲保存目录",
        initialdir=default_dir
    )
    if selected_dir:
        set_music_dir(selected_dir)
        print(f"✅ 歌曲将保存到: {selected_dir}")
    else:
        set_music_dir(default_dir)
        print(f"✅ 歌曲将保存到默认目录: {default_dir}")

# 搜索歌曲模式
def search_mode(driver, base_url, cookie_str, csrf_token, js_ctx):
    while True:
        search_keyword = input("请输入歌曲名称或歌手姓名 (输入 q 退出): ").strip()
        if search_keyword.lower() == 'q':
            break
        # 构造请求URL
        search_url = base_url + f"search/#/?s={quote(search_keyword)}&type=1"
        driver.get(search_url)
        print("正在搜索...")
        search_results = get_search_results(driver)

        if not search_results:
            print("未找到搜索结果")
            continue
        # 根据搜索结果选择下载的歌曲
        while True:
            choice = input("请输入需要下载的歌曲序号 (支持逗号分隔和范围，如 1,3,5-7，输入 q 重新搜索): ").strip()
            if choice.lower() == 'q':
                break
            selected_indices = parse_selections(choice, len(search_results))
            if not selected_indices:
                print("未选择有效的歌曲序号")
                continue
            selected_songs = [song for song in search_results if song["index"] in selected_indices]
            if selected_songs:
                print(f"即将下载 {len(selected_songs)} 首歌曲: {', '.join(s['title'] for s in selected_songs)}")
                choose_save_directory()
                download_songs(cookie_str, csrf_token, js_ctx, selected_songs)
            else:
                print("未找到选择的歌曲")

# 歌单下载模式
def playlist_mode(driver, home_url, cookie_str, csrf_token, js_ctx):
    # 跳转到主页
    if home_url:
        driver.get(home_url)
        print("正在进入个人主页...")
    # 获取歌单
    playlist = get_playlist_titles(driver)
    if playlist:
        # 选择要下载的歌单
        selected = select_playlist(playlist)
        if selected:
            print(f"✅ 正在跳转到歌单: {selected['title']}")
            playlist_url = selected['href']
            music_info = get_music_info(driver, playlist_url)
            if music_info:
                choose_save_directory()
                download_songs(cookie_str, csrf_token, js_ctx, music_info)
            else:
                print("未能获取歌曲信息")
        else:
            print("未选择任何歌单")
    else:
        print("未能获取歌单列表")

def main():
    driver = init()
    base_url = "https://music.163.com/"
    try:
        login_success, home_url = login(driver, base_url)
        if login_success:
            cookie_str, csrf_token = get_cookies(driver)
            # 编译JS代码
            js_ctx = get_js_code()

            while True:
                print("=" * 40)
                print("1. 搜索歌曲下载")
                print("2. 我的歌单下载")
                print("3. 退出")
                print("=" * 40)
                choice = input("请输入选择 (1-3): ").strip()
                if choice == "1":
                    search_mode(driver, base_url, cookie_str, csrf_token, js_ctx)
                elif choice == "2":
                    playlist_mode(driver, home_url, cookie_str, csrf_token, js_ctx)
                elif choice == "3":
                    print("退出程序...")
                    break
                else:
                    print("无效选择，请输入 1-3")
        else:
            print("登录失败")
    except Exception as e:
        print(f"程序出错: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()