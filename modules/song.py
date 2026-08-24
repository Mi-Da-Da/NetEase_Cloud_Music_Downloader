from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

# 获取歌曲信息
def get_music_info(driver, playlist_url):
    print("开始获取歌曲信息")
    driver.get(playlist_url)
    # 切换至主框架
    driver.switch_to.default_content()
    driver.switch_to.frame("g_iframe")
    time.sleep(2)
    # 定位并获取歌曲信息
    wait = WebDriverWait(driver, 20)
    tbody = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.m-table tbody")))
    tr_elements = tbody.find_elements(By.CSS_SELECTOR, "tr")
    print(f"找到 {len(tr_elements)} 首歌曲")

    songs = []
    for i, tr in enumerate(tr_elements, 1):
        try:
            # 从a标签中获取ID
            a_tag = tr.find_element(By.CSS_SELECTOR, "a")
            href = a_tag.get_attribute("href")
            song_id = re.search(r'id=(\d+)', href).group(1) if href else None
            # 从b标签中获取名称
            b_tag = a_tag.find_element(By.CSS_SELECTOR, "b")
            song_name = b_tag.get_attribute("title")
            if song_id and song_name:
                songs.append({'id': song_id, 'title': song_name})
                print(f"{i}. {song_name}")
        except Exception as e:
            print(f"{i}. 提取失败: {e}")

    return songs