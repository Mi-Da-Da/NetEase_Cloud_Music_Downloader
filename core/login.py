from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException, WebDriverException
from webdrivermanager_cn import ChromeDriverManagerAliMirror
import time
import os
import json

# driver_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'chromedriver', 'chromedriver.exe')

def _get_cached_driver_path(project_root):
    """从 driver_cache.json 中读取最近缓存的驱动路径"""
    cache_file = os.path.join(project_root, "chromedriver", ".webdriver", "driver_cache.json")
    if not os.path.exists(cache_file):
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            cache = json.load(f)
        entries = cache.get("chromedriver", {})
        if not entries:
            return None
        # 取 last_read_time 最新的驱动
        latest = max(entries.values(), key=lambda e: e.get("last_read_time", ""))
        path = latest.get("path")
        if path and os.path.exists(path):
            return path
    except Exception:
        pass
    return None

def _create_driver(driver_path, chrome_options):
    """创建 Chrome 驱动实例，成功返回 driver，失败抛出异常"""
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# 浏览器驱动初始化
def init():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # ---------- 阶段 1：优先使用本地缓存驱动（跳过在线检查）----------
    cached_path = _get_cached_driver_path(project_root)
    if cached_path:
        try:
            print(f"使用本地缓存驱动: {cached_path}")
            driver = _create_driver(cached_path, chrome_options)
            print("本地驱动加载成功！")
            driver.set_page_load_timeout(20)
            driver.set_script_timeout(20)
            driver.maximize_window()
            return driver
        except (SessionNotCreatedException, WebDriverException) as e:
            # 典型：版本不匹配（Chrome 更新了）
            print(f"本地驱动不兼容，将重新下载: {str(e)[:100]}")
        except Exception as e:
            print(f"本地驱动加载失败，将重新下载: {str(e)[:100]}")

    # ---------- 阶段 2：本地驱动不可用，在线安装 ----------
    print("正在检测版本并安装驱动（首次使用或浏览器更新后需要）...")
    driver_path = ChromeDriverManagerAliMirror(path=os.path.join(project_root, "chromedriver")).install()
    print("驱动安装完成！")

    driver = _create_driver(driver_path, chrome_options)
    driver.set_page_load_timeout(20)
    driver.set_script_timeout(20)
    driver.maximize_window()

    return driver

def login(driver, url, timeout=60):
    cookie_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cookie.json")

    if os.path.exists(cookie_path):
        try:
            print("正在使用Cookie自动登录...")
            driver.get(url)
            with open(cookie_path, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
            driver.refresh()
            time.sleep(2)
            music_u = driver.get_cookie("MUSIC_U")
            if music_u:
                print("Cookie登录成功")
                home_url = None
                try:
                    user_link = driver.find_element(By.CSS_SELECTOR, "#g-topbar .m-top .wrap .m-tophead a.name")
                    home_url = user_link.get_attribute("href")
                except Exception as e:
                    print(f"未找到用户主页链接（不影响登录）: {e}")
                return True, home_url
            else:
                print("Cookie已失效")
        except Exception as e:
            print("Cookie登录失败:", e)

    print("开始扫码登录...")
    driver.delete_all_cookies()

    # 访问登录页面
    driver.get(url)

    wait = WebDriverWait(driver, 10)
    login_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '登录')]"))
    )
    login_btn.click()
    print("已点击登录按钮，请扫码登录")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            music_u = driver.get_cookie("MUSIC_U")
            if music_u:
                print("登录成功")
                cookies = driver.get_cookies()
                try:
                    os.makedirs(os.path.dirname(cookie_path), exist_ok=True)
                    with open(cookie_path, "w", encoding="utf-8") as f:
                        json.dump(cookies, f, ensure_ascii=False, indent=2)
                    print("Cookie已保存")
                except Exception as e:
                    print(f"Cookie保存失败: {e}")
                driver.refresh()
                time.sleep(3)
                home_url = None
                try:
                    user_link = driver.find_element(By.CSS_SELECTOR, "#g-topbar .m-top .wrap .m-tophead a.name")
                    home_url = user_link.get_attribute("href")
                except Exception as e:
                    print(f"未找到用户主页链接（不影响登录）: {e}")
                return True, home_url
        except Exception as e:
            print(f"登录检测异常: {e}")
            pass
        time.sleep(1)
        print(".", end="", flush=True)
    print("登录超时")

    return False, None

# 获取当前csrf_token和cookies
def get_cookies(driver):
    # 获取cookies
    cookies = driver.get_cookies()
    cookie_str = "; ".join(
        f"{c['name']}={c['value']}"
        for c in cookies
    )
    # 获取csrf_tokens
    csrf_token = driver.get_cookie('__csrf')
    if csrf_token:
        return cookie_str, csrf_token['value']
    else:
        print("未找到csrf_token")
        return None, None