from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import re

def get_search_results(driver):
    wait = WebDriverWait(driver, 10)
    try:
        # 切换到当前框架
        driver.switch_to.default_content()
        driver.switch_to.frame("g_iframe")
        time.sleep(2)
        # 获取歌单元素
        result_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".srchsongst"))
        )
        div_elements = result_element.find_elements(By.CSS_SELECTOR, ".item.f-cb.h-flag")
        # 显示搜索结果
        results = []
        for i, div in enumerate(div_elements, 1):
            try:
                a_tags = div.find_elements(By.CSS_SELECTOR, "a")
                href = a_tags[1].get_attribute("href")
                song_id = re.search(r'id=(\d+)', href).group(1) if href else None
                # 从b标签中获取名称
                b_tag = a_tags[1].find_element(By.CSS_SELECTOR, "b")
                # 获取 title 属性
                song_name = b_tag.get_attribute("title")
                singer = ""
                album = ""
                # 获取歌手名称
                for a in a_tags:
                    data_log_json = a.get_attribute("data-log-json")
                    if not data_log_json:
                        continue
                    match = re.search(r'"resource_type":"([^"]+)"', data_log_json)
                    if match and match.group(1) == "artist":
                        singer = a.text.strip()
                    elif match and match.group(1) == "album":
                        album = a.text.strip()
                        break
                results.append({'index': i, 'id': song_id, 'title': song_name})
                print(f"{i}. {song_name}  {singer}  {album}")
            except Exception as e:
                print(f"{i}. 未找到: {e}")

        return results
    except Exception as e:
        print(f"等待超时: {e}")
        return []