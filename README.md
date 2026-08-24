# 网易云音乐批量下载工具

基于 Selenium + 网易云官方 API 的命令行批量下载工具。扫码登录后，支持**搜索歌曲下载**和**我的歌单批量下载**，使用 8 线程并发加速，自动跳过已下载歌曲，并以 `exhigh`（极高）音质请求下载链接。

---

## ✨ 功能特性

- 🔐 **扫码登录 + Cookie 持久化**：首次扫码后自动保存 Cookie，下次启动直接免扫码登录（失效时自动回退到扫码）
- 🎵 **两种下载模式**：关键词搜索下载 / 个人歌单一键全量下载
- ⚡ **8 线程并发下载**：配合 tqdm 实时进度条，显示成功 / 失败 / 跳过计数
- 🚫 **自动去重**：保存目录中已存在同名 `.mp3` 时自动跳过
- 🧹 **非法文件名自动清洗**：自动去除 `\ / : * ? " < > |` 等 Windows 非法字符
- 🎚️ **极高音质优先**：API 请求级别使用 `exhigh` / `encodeType=aac`
- ⚙️ **智能驱动管理**：首次自动下载匹配 Chrome 版本的 ChromeDriver（阿里云镜像加速），之后优先使用本地缓存，跳过在线检查秒启动
- 📂 **自定义保存目录**：GUI 选择器（Tkinter）手动选择下载保存路径

---

## 📁 目录结构

```
网易云音乐/
├── core/
│   ├── login.py                   # 浏览器初始化 / 扫码登录 / Cookie 读写 / ChromeDriver 智能管理
│   ├── encrypt.py                 # JS 加密编译、调用网易云 weapi 获取歌曲直链
│   └── 网易云.js                   # 网易云 API d/aes 加密算法（由 core/encrypt.py 加载执行）
├── modules/
│   ├── playlist.py                # 登录后获取"我的歌单"列表 + 交互式选择
│   ├── song.py                    # 进入歌单页解析全部歌曲的 id / 标题 / 歌手
│   ├── search.py                  # 搜索结果页解析（序号、标题、歌手、专辑）
│   └── downloader.py              # 下载单首歌曲 / 去重检查 / 文件名清洗 / 保存目录管理
├── data/
│   ├── music/                     # 默认下载目录（可运行时切换）
│   └── cookie.json                # 登录 Cookie 缓存（首次扫码登录后自动生成）
├── chromedriver/
│   └── .webdriver/                # webdrivermanager_cn 本地驱动缓存
│       ├── driver_cache.json      # 驱动版本索引（init() 从此读取，实现秒启动）
│       └── chromedriver/<版本>/   # 已下载的 chromedriver.exe
├── music_downloader.py            # 程序主入口（菜单调度 / 多线程下载 / 进度展示）
├── requirements.txt               # Python 依赖清单（pip install -r requirements.txt）
└── Readme.md
```

---

## 🔧 环境要求

| 依赖 | 最低版本 | 说明 |
|---|---|---|
| Python | 3.8+ | 测试运行于 3.12 |
| Google Chrome | 最新稳定版 | 驱动自动匹配当前已安装的 Chrome 版本 |
| Node.js | 14+ | PyExecJS 运行时，用于执行 `网易云.js` 的 weapi 加密代码 |
| Windows | 10 / 11 | 当前路径写死 `chromedriver-win64` 结构，仅支持 Windows x64 |

> 注：Tkinter 为 Python Windows 官方安装包自带组件，无需额外 pip 安装。

---

## 📦 安装步骤

### 1. 安装 Python 依赖

项目根目录下提供了 `requirements.txt`，直接一键安装：

```bash
pip install -r requirements.txt
```

依赖一览（仅供查阅，无需手动逐个安装）：

| 包名 | 用途 |
|---|---|
| `selenium` | 浏览器自动化（登录 / 搜索 / 歌单解析） |
| `requests` | 下载 MP3 文件 + 调用 weapi 获取歌曲直链 |
| `PyExecJS` | 编译执行 `网易云.js` 完成 API 参数加密 |
| `tqdm` | 多线程下载进度条 |
| `webdrivermanager_cn` | ChromeDriver 自动下载与版本匹配（阿里云镜像，国内加速） |

> 想锁定完全一致的精确版本时，可在本机正常运行后执行 `pip freeze > requirements.txt` 覆盖本文件即可。

### 2. 安装 Node.js

PyExecJS 必须依赖外部 JS 运行时来执行网易云的加密算法：

1. 前往 [Node.js 官网](https://nodejs.org/) 下载 **LTS 版本**并安装
2. 安装完成后在终端验证：

```bash
node -v
# 示例输出：v20.18.0
```

如果 `node` 命令不可用，请检查系统 `PATH` 环境变量是否包含 Node.js 安装目录。

---

## 🚀 使用方法

### 启动程序

```bash
python music_downloader.py
```

#### 启动阶段发生了什么

1. **驱动加载**：
   - 优先读取 `chromedriver/.webdriver/driver_cache.json` 中的本地缓存驱动 → 直接使用（秒启动，不联网）
   - 若本地缓存缺失或与 Chrome 版本不兼容 → 使用 `webdrivermanager_cn` 的**阿里云镜像**自动下载匹配版本
   - 下载结果会自动写入缓存，下次启动恢复秒开
2. **登录**：
   - 读取 `data/cookie.json` → 注入浏览器 → 刷新后检测 `MUSIC_U` 字段
   - Cookie 有效 → 直接进入主菜单
   - Cookie 失效 / 不存在 → 弹出浏览器，请用 **网易云音乐 App 扫码登录**（60 秒超时），登录成功后自动写回新 Cookie

### 主菜单

```
========================================
1. 搜索歌曲下载
2. 我的歌单下载
3. 退出
========================================
请输入选择 (1-3):
```

#### 模式 1：搜索歌曲下载

1. 输入歌曲名称或歌手，例如 `周杰伦`、`晴天`
2. 程序在网易云搜索页加载结果并解析为带序号的列表
3. 选择要下载的序号，支持以下写法：
   | 输入示例 | 含义 |
   |---|---|
   | `3` | 只下第 3 首 |
   | `1,3,5` | 下第 1、3、5 首 |
   | `1-5` | 下第 1 到第 5 首（含首尾） |
   | `1,3,5-7` | 混合写法，下 1、3、5、6、7 |
   | `q` | 退出当前搜索，重新输入关键词 |
4. 弹出目录选择对话框 → 选定后开始多线程下载

#### 模式 2：我的歌单下载

1. 程序自动跳转到登录用户的网易云个人主页
2. 解析所有自建 / 收藏歌单为带序号列表
3. 输入歌单序号 → 进入歌单详情页解析全部歌曲
4. 选择保存目录 → 歌单内全部歌曲开始批量下载

### 下载进度与结果示例

```
歌曲总数: 30 首
成功下载: 27 首
已下载: 2 首        ← 已存在文件自动跳过
下载失败: 1 首
❌ 以下歌曲下载失败：
1. 某版权受限歌曲
```

---

## 🧠 关键实现细节

### ChromeDriver 智能管理（`core/login.py::init()`）

为解决 `webdrivermanager_cn` **每次启动都联网检查版本、启动慢**的问题，采用两阶段策略：

```
阶段 1 ──► 读 driver_cache.json ──► 文件存在? ──► 是 ──► 直接 new Chrome() ──► 返回
               │
               └ 否 / 抛 SessionNotCreatedException
                      │
                      ▼
阶段 2 ──► ChromeDriverManagerAliMirror(path=./chromedriver).install()
               │
               └ 下载 & 解压 → 写回 driver_cache.json → new Chrome() → 返回
```

- **首次启动**：走阶段 2，从阿里云镜像下载（国内比官方 Google 源快很多）
- **后续启动**：99% 概率走阶段 1，纯本地操作，**无需联网**
- **Chrome 浏览器自动升级后**：阶段 1 会捕获 `SessionNotCreatedException`，自动降级到阶段 2 重新下载匹配版本

### Cookie 登录机制（`core/login.py::login()`）

1. `data/cookie.json` 存在时，先 `driver.get(url)` 打开主页 → 逐条 `add_cookie` → `refresh`
2. 检测 `MUSIC_U` 这个关键 Cookie 是否存在
3. 存在 → 解析顶部导航栏 `.m-tophead a.name` 的 `href` 作为个人主页 URL 并返回登录成功
4. 不存在 / 异常 → `delete_all_cookies` → 点击页面"登录"按钮 → 弹出二维码 → 轮询 `MUSIC_U`（最多 60 秒）
5. 扫码成功后把全部 Cookie 序列化到 `data/cookie.json`

### API 参数加密（`core/encrypt.py` + `网易云.js`）

网易云 `weapi/song/enhance/player/url/v1` 接口的 `params` / `encSecKey` 参数使用 d(aes) + rsa 加密：

1. `get_js_code()`：用 `execjs.compile()` 加载 `网易云.js` 并返回上下文
2. `get_music_url(...)`：构造 `{csrf_token, encodeType:"aac", ids:[id], level:"exhigh"}` → 调 JS 的 `get_data()` 完成加密 → `requests.post` → 取 `json["data"][0]["url"]` 作为直链

> `level=exhigh` 代表极高音质，但**最终能否拿到高码率资源取决于该账号的 VIP / 黑胶状态**以及歌曲本身的版权开放情况。

### 多线程下载（`music_downloader.py::download_songs()`）

- `ThreadPoolExecutor(max_workers=8)` 并发
- 每首歌独立调 `modules/downloader.py::download_song()`，内部做：
  1. `is_song_exist(title)` → 命中则返回 `{"skipped":True}`
  2. `get_music_url(...)` → 无直链则返回失败
  3. `save(title, url)` → 流式写入 8KB chunk → 成功
- `tqdm` + `as_completed` 实时更新进度条后缀：`成功 / 失败 / 跳过`

---

## ❓ 常见问题 & 故障排查

### 1. 报错 `session not created: This version of ChromeDriver only supports Chrome version XXX`

**原因**：Chrome 浏览器后台自动升级，本地缓存的 ChromeDriver 版本落后。

**解决**：
- 方案 A（推荐）：什么都不用做。当前 `init()` 已经捕获 `SessionNotCreatedException`，会自动下载与新 Chrome 匹配的驱动版本，**下次启动即恢复正常**。
- 方案 B（手动强制）：删除整个 `chromedriver/.webdriver/` 目录后重新运行，程序会视为首次启动并重新下载。

### 2. 报错 `RuntimeError: Couldn't find a suitable runtime`

**原因**：PyExecJS 找不到可用的 JS 运行时（Node.js 未安装或未加入 PATH）。

**解决**：
1. 确认已安装 Node.js LTS
2. 新开一个终端，运行 `node -v` 是否有输出版本号
3. 如果 `node -v` 在新终端可用、但 PyCharm / VSCode 的终端不可用 → 重启 IDE，让环境变量重新加载
4. Windows 上若 `node -v` 仍不可用 → 手动把 `C:\Program Files\nodejs\` 加入系统 `PATH`

### 3. 启动时一直卡在"正在检测版本并安装驱动"

**原因**：网络环境访问阿里云镜像受阻（校园网 / 公司代理 / 无外网）。

**解决**：
1. 确保网络能访问 `registry.npmmirror.com`（webdrivermanager_cn 默认阿里云镜像源）
2. 若网络受限，可**手动下载对应版本 ChromeDriver**：
   - 打开 Chrome → 设置 → 关于 Chrome → 查看版本号（如 `151.0.7922.138`）
   - 到 [Chrome for Testing 镜像](https://registry.npmmirror.com/binary.html?path=chrome-for-testing/) 下载对应 `chromedriver-win64.zip`
   - 解压后把 `chromedriver.exe` 放到任意位置，然后修改 `core/login.py` 开头的注释行：
     ```python
     # 改为你本地的实际路径，然后直接在 init() 里用这个 driver_path
     driver_path = r"D:\path\to\chromedriver.exe"
     ```

### 4. 扫码登录后仍然提示"Cookie已失效" / 回到扫码页面

**原因**：多为扫码成功但网络/页面刷新时序问题，或者保存的 Cookie 中 `MUSIC_U` 未生成。

**解决**：
1. 删除 `data/cookie.json`，重新运行
2. 扫码登录时，**等待浏览器页面完全跳转到已登录状态**再关闭二维码弹窗
3. 如果频繁出现，检查系统时间是否准确，Cookie 带有时间戳校验。

### 5. 很多歌曲下载失败，日志打印"歌曲 xxxxx 无下载链接"

**原因**：网易云官方 weapi 返回的 `url` 字段为 `null`。常见场景：
- 该歌曲仅 VIP 可听，当前登录账号无会员
- 歌曲因版权原因下架 / 仅限特定地区收听
- 部分独立音乐人作品未开放外链

**解决**：这是服务端限制，程序无法绕过。请升级账号或换其他歌曲。

### 6. 下载的 mp3 都是 0 字节 / 无法播放

**原因**：`requests.get` 写文件时中途网络断开，或获取到的直链本身是跳转/鉴权失败。

**解决**：
1. 删除 0 字节的文件
2. 重新运行程序，由于自动去重，已下载的正常歌曲不会重复下载，会重新下载失败的部分
3. 若频繁出现，考虑在 `modules/downloader.py::save()` 中加入写入成功后文件大小校验（<10KB 视为失败并自动删除）

### 7. 登录超时（60 秒内没扫完）

默认 `login(timeout=60)`。如需更长时间，修改 `core/login.py::login(driver, url, timeout=60)` 的 `timeout` 参数，或在调用处（`music_downloader.py` 第 172 行）传更大的值。

---

## 📌 注意事项

1. **本工具仅用于个人学习与已购/免费音乐的离线备份，请遵守网易云音乐用户协议与版权法规，勿用于批量爬取 / 商用 / 二次分发。**
2. 频繁大量调用 weapi 可能触发风控，导致临时需要人机验证或账号被限流。建议单次下载量控制在 200 首以内。
3. `data/cookie.json` 内含登录凭证，**请勿上传到公开仓库或分享给他人**。
