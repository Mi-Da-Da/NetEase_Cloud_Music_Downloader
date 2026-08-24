import requests
import execjs
import os

def get_js_code():
    js_path = os.path.join(os.path.dirname(__file__), '网易云.js')
    js_code = execjs.compile(open(js_path, encoding='utf-8').read())
    return js_code

# 获取歌曲URL
def get_music_url(cookie_str, csrf_token, js_ctx, music_id):
    music_link = 'https://music.163.com/weapi/song/enhance/player/url/v1'
    # 构造请求头部
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        "Referer": "https://music.163.com/",
        'cookie': cookie_str
    }
    # 查询参数
    params = {
        'csrf_token': csrf_token
    }
    # 获取加密参数
    idx = {
        'csrf_token': csrf_token,
        'encodeType': "aac",
        'ids': f"[{music_id}]",
        'level': "exhigh"
    }
    data = js_ctx.call("get_data", idx)
    # 请求参数，加密，需要通过js生成
    resp_data = requests.post(url=music_link, params=params, data=data, headers=headers)
    json_data = resp_data.json()
    music_url = json_data["data"][0]["url"]
    if music_url is None:
        print(f"歌曲 {music_id} 无下载链接")

    return music_url