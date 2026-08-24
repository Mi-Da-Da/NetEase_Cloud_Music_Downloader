from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time

# 获取歌单标题
def get_playlist_titles(driver):
    wait = WebDriverWait(driver, 10)
    try:
        # 切换到当前框架
        driver.switch_to.default_content()
        driver.switch_to.frame("g_iframe")
        time.sleep(2)
        # 获取歌单元素
        ul_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.m-cvrlst.f-cb"))
        )
        li_elements = ul_element.find_elements(By.CSS_SELECTOR, "li")
        print(f"找到 {len(li_elements)} 个歌单")
        # 显示歌单
        playlist = []
        for i, li in enumerate(li_elements, 1):
            try:
                a_tag = li.find_element(By.CSS_SELECTOR, "a.msk")
                title = a_tag.get_attribute("title")
                href = a_tag.get_attribute("href")
                if title:
                    playlist.append({
                        'index': i,
                        'title': title,
                        'href': href
                    })
                    print(f"{i}. {title}")
            except Exception as e:
                print(f"{i}. 未找到 a.msk: {e}")

        return playlist
    except Exception as e:
        print(f"等待超时: {e}")
        return []

# 用户选择歌单
def select_playlist(playlist):
    if not playlist:
        print("没有可用的歌单")
        return None
    print("请选择歌单：")
    while True:
        choice = input(f"请输入序号 (1-{len(playlist)})，输入 q 退出: ").strip()
        if choice.lower() == 'q':
            return None
        try:
            idx = int(choice)
            if 1 <= idx <= len(playlist):
                return playlist[idx - 1]
            else:
                print(f"请输入 1-{len(playlist)} 之间的数字")
        except ValueError:
            print("请输入有效的数字")