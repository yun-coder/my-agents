# 浏览器自动化 × Stealth 反检测技术 — 综合实战 Demo

## 概述

本 Demo 将 **浏览器自动化**（Playwright 框架）与 **浏览器 Stealth 反检测技术**深度结合，展示如何构建一个"难以被网站识别为自动化工具"的浏览器操作引擎。内容从底层反检测原理到上层业务自动化逐层递进，覆盖十余种真实反检测场景。

---

## 目录

1. [为什么需要 Stealth？—— 自动化检测的原理](#1-为什么需要-stealth自动化检测的原理)
2. [Stealth 技术全景图](#2-stealth-技术全景图)
3. [实战 Demo 1：基础 Stealth 浏览器工厂](#3-实战-demo-1基础-stealth-浏览器工厂)
4. [实战 Demo 2：指纹伪装 — Canvas、WebGL、Font、Audio 指纹欺骗](#4-实战-demo-2指纹伪装canvaswebglfontaudio-指纹欺骗)
5. [实战 Demo 3：人类行为模拟器](#5-实战-demo-3人类行为模拟器)
6. [实战 Demo 4：动态代理与 IP 轮换](#6-实战-demo-4动态代理与-ip-轮换)
7. [实战 Demo 5：自动化检测页面综合测试](#7-实战-demo-5自动化检测页面综合测试)
8. [实战 Demo 6：生产级 Stealth Agent 框架](#8-实战-demo-6生产级-stealth-agent-框架)
9. [自动化检测的对抗手段总结](#9-自动化检测的对抗手段总结)
10. [附录：检测网站清单 & Playwright Stealth 插件](#10-附录)

---

## 1. 为什么需要 Stealth？—— 自动化检测的原理

网站通过以下 **指纹维度** 来区分人类用户和自动化工具：

| 检测维度 | 检测内容 | Playwright 默认暴露问题 |
|---------|---------|----------------------|
| `navigator.webdriver` | 是否存在自动化标记 | Playwright 默认设置为 `true` ❌ |
| `navigator.plugins` | 浏览器插件列表 | 自动化环境通常为空数组 |
| `chrome` 对象 | 是否暴露 `window.chrome` | 无头模式缺失 |
| `navigator.languages` | 语言列表 | 通常只返回 `["en-US"]` |
| WebGL 指纹 | 显卡渲染器信息 | 无头模式渲染器包含"SwiftShader"关键字 |
| Canvas 指纹 | 画布渲染特征 | 与真实浏览器不同 |
| AudioContext 指纹 | 音频处理栈特征 | 无头模式缺失 |
| 字体列表 | 系统可用字体 | 无头模式只有很少的系统字体 |
| 屏幕/视口特征 | 分辨率、色深等 | 默认窗口小，色深等可能异常 |
| 时间/时区 | `Date` 对象行为 | 默认 UTC 时区 |
| 权限状态 | 麦克风、摄像头等 | 权限可能不完整 |
| 行为模式 | 鼠标轨迹、滚动模式、点击间隔 | 自动化操作缺少人类随机性 |

---

## 2. Stealth 技术全景图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Stealth 反检测技术栈                           │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: 启动参数伪装                                           │
│  ├── --disable-blink-features=AutomationControlled               │
│  ├── --disable-features=IsolateOrigins,site-per-process           │
│  └── --flag-switches-begin --flag-switches-end                    │
│                                                                   │
│  Layer 2: 浏览器上下文伪装                                       │
│  ├── 真实 User-Agent（与操作系统匹配）                            │
│  ├── 真实视口尺寸 (1920x1080 / 1440x900 等)                      │
│  ├── 时区 / 地区 / 语言 匹配目标网站                              │
│  ├── 地理位置权限 & 坐标                                         │
│  └── 设备缩放因子 (deviceScaleFactor)                              │
│                                                                   │
│  Layer 3: JavaScript 特征覆盖 (add_init_script)                  │
│  ├── navigator.webdriver → undefined                              │
│  ├── navigator.plugins → 模拟真实插件列表                         │
│  ├── navigator.languages → 匹配地区                                │
│  ├── window.chrome → 全部子对象                                    │
│  ├── navigator.hardwareConcurrency → 真实 CPU 核心数              │
│  ├── navigator.deviceMemory → 真实内存大小                         │
│  ├── navigator.connection → 模拟网络类型                            │
│  ├── WebGL renderer → 替换为真实显卡厂商信息                      │
│  └── Canvas → 添加微小噪声（指纹一致性）                          │
│                                                                   │
│  Layer 4: 人类行为模拟                                            │
│  ├── 鼠标移动贝塞尔曲线轨迹                                       │
│  ├── 随机滚动模式 (带加速度和停顿)                                 │
│  ├── 输入间隔随机化 (每个字符 50-200ms)                            │
│  ├── 点击前悬停 (100-500ms)                                       │
│  ├── 页面停留时间 (随机 3-15 秒)                                  │
│  └── Tab 切换 / 失焦事件                                          │
│                                                                   │
│  Layer 5: 网络层伪装                                              │
│  ├── 动态代理轮换 (Proxy rotation)                                │
│  ├── 请求头顺序调整 (HTTP header 顺序指纹)                        │
│  ├── 自定义 Accept-Language / Accept-Encoding                     │
│  ├── 拦截 WebDriver 相关的请求头                                   │
│  └── 使用住宅代理而非数据中心代理                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 实战 Demo 1：基础 Stealth 浏览器工厂

构建一个工厂函数，统一生产带有 Stealth 配置的浏览器实例。

```python
"""
stealth_browser_factory.py
基础 Stealth 浏览器工厂 — 生产带有反检测配置的浏览器实例。
"""
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StealthFactory")


@dataclass
class StealthConfig:
    """Stealth 配置数据类。"""
    viewport_width: int = 1920
    viewport_height: int = 1080
    device_scale_factor: float = 1.0
    locale: str = "zh-CN"
    timezone_id: str = "Asia/Shanghai"
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
    headless: bool = True
    proxy: Optional[dict] = None
    geolocation: Optional[dict] = field(default_factory=lambda: {
        "latitude": 39.9042,
        "longitude": 116.4074,
    })
    permissions: list[str] = field(default_factory=lambda: [
        "geolocation", "notifications"
    ])
    extra_args: list[str] = field(default_factory=lambda: [
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--disable-web-security",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-infobars",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-field-trial-config",
        "--disable-ipc-flooding-protection",
        "--window-size=1920,1080",
        "--start-maximized",
    ])
    # 模拟真实浏览器的插件数量
    plugins_count: int = 5
    # 模拟 CPU 核心数
    hardware_concurrency: int = 8
    # 模拟设备内存 (GB)
    device_memory: int = 8


class StealthBrowserFactory:
    """Stealth 浏览器工厂 — 统一生产反检测配置的浏览器。"""

    def __init__(self, config: Optional[StealthConfig] = None):
        self.config = config or StealthConfig()

    async def create_browser(self) -> Browser:
        """创建带有启动参数伪装的浏览器实例。"""
        logger.info("启动浏览器 (headless=%s)", self.config.headless)
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=self.config.headless,
            args=self.config.extra_args,
        )
        return browser

    async def create_stealth_context(self, browser: Browser) -> BrowserContext:
        """创建带有全面 Stealth 配置的浏览器上下文。"""
        context_options = {
            "viewport": {
                "width": self.config.viewport_width,
                "height": self.config.viewport_height,
            },
            "device_scale_factor": self.config.device_scale_factor,
            "user_agent": self.config.user_agent,
            "locale": self.config.locale,
            "timezone_id": self.config.timezone_id,
            "permissions": self.config.permissions,
        }

        # 添加地理位置
        if self.config.geolocation:
            context_options["geolocation"] = self.config.geolocation

        # 添加代理
        if self.config.proxy:
            context_options["proxy"] = self.config.proxy

        context = await browser.new_context(**context_options)

        # ===== 注入核心 Stealth 脚本 =====
        await context.add_init_script(f"""
            // ===== 1. 覆盖 navigator.webdriver =====
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined,
            }});

            // ===== 2. 覆盖 navigator.plugins =====
            Object.defineProperty(navigator, 'plugins', {{
                get: () => {self._generate_plugins_js()},
            }});

            // ===== 3. 覆盖 navigator.languages =====
            Object.defineProperty(navigator, 'languages', {{
                get: () => ['{self.config.locale}', 'zh', 'en'],
            }});

            // ===== 4. 构造 window.chrome 对象 =====
            window.chrome = {{
                runtime: {{}},
                loadTimes: function() {{}},
                csi: function() {{ return {{}}; }},
                app: {{ isInstalled: false, InstallState: {{ DISABLED: 'disabled' }}, RunningState: {{ CANNOT_RUN: 'cannot_run' }} }},
                webstore: {{ onInstallStageChanged: {{ addListener: function() {{}} }}, onDownloadProgress: {{ addListener: function() {{}} }} }},
                runtimeOnConnect: {{ addListener: function() {{}} }},
            }};

            // ===== 5. 覆盖硬件信息 =====
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {self.config.hardware_concurrency},
            }});
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {self.config.device_memory},
            }});

            // ===== 6. 覆盖权限状态 =====
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => {{
                if (parameters.name === 'notifications') {{
                    return Promise.resolve({{ state: Notification.permission }});
                }}
                return originalQuery(parameters);
            }};

            // ===== 7. 覆盖 WebGL 指纹 =====
            const getParameterProxyHandler = {{
                apply: function(target, thisArg, args) {{
                    const param = args[0];
                    const webglParams = {{
                        37445: "ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 (0x2484) Direct3D11 vs_5_0 ps_5_0)",
                        37446: "NVIDIA GeForce RTX 3070",
                        7936: "WebKit WebGL",
                        7937: "OpenGL ES 2.0 (ANGLE 2.1.0.24506)",
                    }};
                    if (param in webglParams) {{
                        return webglParams[param];
                    }}
                    return target.apply(thisArg, args);
                }}
            }};
            try {{
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                if (gl) {{
                    const origGetParameter = gl.getParameter.bind(gl);
                    gl.getParameter = new Proxy(gl.getParameter, getParameterProxyHandler);
                }}
            }} catch(e) {{}}

            // ===== 8. 覆盖 Canvas 指纹 (添加微小噪声) =====
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type, quality) {{
                const canvas = document.createElement('canvas');
                canvas.width = this.width;
                canvas.height = this.height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(this, 0, 0);
                // 在特定位置添加一个像素的微小偏移
                const imageData = ctx.getImageData(0, 0, 1, 1);
                imageData.data[0] = Math.min(255, imageData.data[0] + 1);
                ctx.putImageData(imageData, 0, 0);
                return originalToDataURL.call(canvas, type, quality);
            }};
        """)

        logger.info("Stealth 浏览器上下文已创建")
        return context

    async def create_page(self, context: BrowserContext) -> Page:
        """在 Stealth 上下文中创建页面。"""
        page = await context.new_page()
        # 额外：覆盖页面级别的 Permission API
        await page.goto("about:blank")
        return page

    def _generate_plugins_js(self) -> str:
        """生成模拟的插件列表 JavaScript 代码。"""
        count = self.config.plugins_count
        plugins = []
        plugin_names = [
            ("Chrome PDF Plugin", "Portable Document Format", ["pdf"]),
            ("Chrome PDF Viewer", "pdf", ["pdf"]),
            ("Native Client", "Native Client Executable", ["nexe", "pexe"]),
            ("Widevine Content Decryption Module", "Enables Widevine licenses", ["widevine"]),
        ]
        for i in range(min(count, len(plugin_names))):
            name, desc, exts = plugin_names[i]
            plugins.append(f'{{ name: "{name}", description: "{desc}", filename: "{name}.dll", length: 1 }}')
        return f"[{', '.join(plugins)}]"


# ===== 使用示例 =====
async def demo_stealth_factory():
    """演示如何使用 Stealth 浏览器工厂。"""
    config = StealthConfig(
        viewport_width=1920,
        viewport_height=1080,
        locale="zh-CN",
        timezone_id="Asia/Shanghai",
        headless=True,
        hardware_concurrency=16,
        device_memory=8,
    )
    factory = StealthBrowserFactory(config)
    browser = await factory.create_browser()
    context = await factory.create_stealth_context(browser)
    page = await factory.create_page(context)

    # 访问检测页面验证 Stealth 效果
    await page.goto("https://bot.sannysoft.com", wait_until="networkidle")
    await page.screenshot(path="./screenshots/stealth_factory_test.png", full_page=True)
    logger.info("Stealth 测试截图已保存")

    # 在检测页面注入额外检查
    stealth_report = await page.evaluate("""
        () => ({
            webdriver: navigator.webdriver,
            pluginsLength: navigator.plugins.length,
            languages: navigator.languages,
            hardwareConcurrency: navigator.hardwareConcurrency,
            deviceMemory: navigator.deviceMemory,
            hasChrome: typeof window.chrome !== 'undefined',
            hasChromeRuntime: typeof window.chrome.runtime !== 'undefined',
        })
    """)
    logger.info("Stealth 检查结果: %s", stealth_report)

    await browser.close()
    logger.info("浏览器已关闭")


if __name__ == "__main__":
    asyncio.run(demo_stealth_factory())
```

---

## 4. 实战 Demo 2：指纹伪装 — Canvas、WebGL、Font、Audio 指纹欺骗

网站常用 **浏览器指纹**（Browser Fingerprinting）技术来识别访问者。即使清除了 Cookie，指纹也能追踪用户。我们需要在自动化环境中伪装这些指纹。

```python
"""
fingerprint_spoofer.py
浏览器指纹伪装引擎 — 覆盖 Canvas、WebGL、Font、Audio 等指纹特征。
"""
import asyncio
import json
import math
import random
from dataclasses import dataclass, field
from typing import Any

from playwright.async_api import async_playwright, BrowserContext


@dataclass
class FingerprintProfile:
    """指纹配置文件 — 定义要模拟的浏览器指纹特征。"""
    # WebGL 信息
    webgl_vendor: str = "Google Inc. (NVIDIA)"
    webgl_renderer: str = "ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0)"
    webgl_unmasked_vendor: str = "NVIDIA Corporation"
    webgl_unmasked_renderer: str = "NVIDIA GeForce RTX 3070"
    
    # Canvas 噪声参数 (每像素添加 ±0-2 的偏移)
    canvas_noise_level: float = 1.0
    
    # AudioContext 噪声参数
    audio_noise_level: float = 0.0001
    
    # 字体列表 (指纹用)
    fonts: list[str] = field(default_factory=lambda: [
        "Arial", "Helvetica", "Times New Roman", "Courier New", "Verdana",
        "Georgia", "Palatino Linotype", "Tahoma", "Trebuchet MS", "Microsoft YaHei",
        "SimSun", "SimHei", "Microsoft JhengHei",
    ])
    
    # 屏幕信息
    screen_color_depth: int = 24
    screen_pixel_depth: int = 24
    
    # 平台信息
    platform: str = "Win32"
    oscpu: str = "Windows NT 10.0; Win64; x64"
    
    # Do Not Track
    do_not_track: Optional[str] = "1"


class FingerprintSpoofer:
    """浏览器指纹伪装引擎。"""

    def __init__(self, profile: Optional[FingerprintProfile] = None):
        self.profile = profile or FingerprintProfile()

    async def apply_to_context(self, context: BrowserContext) -> None:
        """将指纹伪装注入到浏览器上下文。"""
        profile_json = json.dumps({
            "webglVendor": self.profile.webgl_vendor,
            "webglRenderer": self.profile.webgl_renderer,
            "webglUnmaskedVendor": self.profile.webgl_unmasked_vendor,
            "webglUnmaskedRenderer": self.profile.webgl_unmasked_renderer,
            "canvasNoiseLevel": self.profile.canvas_noise_level,
            "audioNoiseLevel": self.profile.audio_noise_level,
            "fonts": self.profile.fonts,
            "colorDepth": self.profile.screen_color_depth,
            "pixelDepth": self.profile.screen_pixel_depth,
            "platform": self.profile.platform,
            "oscpu": self.profile.oscpu,
            "doNotTrack": self.profile.do_not_track,
            "seed": random.randint(1, 1000000),
        })

        await context.add_init_script(f"""
            (() => {{
                const profile = {profile_json};

                // ==========================================
                // 1. WebGL 指纹欺骗
                // ==========================================
                const webglParams = {{
                    37445: profile.webglVendor,      // UNMASKED_VENDOR_WEBGL
                    37446: profile.webglRenderer,     // UNMASKED_RENDERER_WEBGL
                    7936: "WebKit WebGL",             // VENDOR
                    7937: "OpenGL ES 2.0 (ANGLE 2.1.0.24506)",  // RENDERER
                    3415: "WebGL 1.0 (OpenGL ES 2.0 Chromium)",
                    33901: "WebGL 1.0 (OpenGL ES 2.0 Chromium)",  // VERSION
                    34921: "WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)",  // SHADING_LANGUAGE_VERSION
                }};

                // 覆盖 WebGLRenderingContext.getParameter
                const canvasEl = document.createElement('canvas');
                const webglCtx = canvasEl.getContext('webgl') || canvasEl.getContext('experimental-webgl');
                if (webglCtx) {{
                    const origGetParam = webglCtx.getParameter.bind(webglCtx);
                    webglCtx.getParameter = function(param) {{
                        if (param in webglParams) {{
                            return webglParams[param];
                        }}
                        if (param === 35724) {{  // ALIASED_LINE_WIDTH_RANGE
                            return new Float32Array([1, 1]);
                        }}
                        return origGetParam(param);
                    }};

                    // 覆盖 getExtension 以返回真实扩展
                    const origGetExt = webglCtx.getExtension.bind(webglCtx);
                    webglCtx.getExtension = function(name) {{
                        const ext = origGetExt(name);
                        if (ext) return ext;
                        // 返回常见的 WebGL 扩展
                        const fakeExts = {{
                            'EXT_texture_filter_anisotropic': {{}},
                            'WEBGL_debug_renderer_info': {{
                                UNMASKED_VENDOR_WEBGL: profile.webglUnmaskedVendor,
                                UNMASKED_RENDERER_WEBGL: profile.webglUnmaskedRenderer,
                            }},
                        }};
                        return fakeExts[name] || null;
                    }};
                }}

                // 覆盖 WebGL2RenderingContext
                const webgl2Ctx = canvasEl.getContext('webgl2');
                if (webgl2Ctx) {{
                    const origGetParam2 = webgl2Ctx.getParameter.bind(webgl2Ctx);
                    webgl2Ctx.getParameter = function(param) {{
                        if (param in webglParams) {{
                            return webglParams[param];
                        }}
                        return origGetParam2(param);
                    }};
                }}

                // ==========================================
                // 2. Canvas 指纹噪声注入
                // ==========================================
                const noiseLevel = profile.canvasNoiseLevel;
                const canvasSeed = profile.seed;

                // 重写 CanvasRenderingContext2D 的关键方法
                const proto = CanvasRenderingContext2D.prototype;

                // 对 fillText / strokeText 加入噪声
                const origFillText = proto.fillText;
                proto.fillText = function(text, x, y, maxWidth) {{
                    // 在一定概率下微调绘制坐标
                    const noiseX = (Math.sin(canvasSeed + x) * noiseLevel);
                    const noiseY = (Math.cos(canvasSeed + y) * noiseLevel);
                    return origFillText.call(this, text, x + noiseX, y + noiseY, maxWidth);
                }};

                const origStrokeText = proto.strokeText;
                proto.strokeText = function(text, x, y, maxWidth) {{
                    const noiseX = (Math.sin(canvasSeed + x) * noiseLevel);
                    const noiseY = (Math.cos(canvasSeed + y) * noiseLevel);
                    return origStrokeText.call(this, text, x + noiseX, y + noiseY, maxWidth);
                }};

                // 对 getImageData 加入像素噪声 (仅在 toDataURL 层级加)
                // 同时覆盖 toDataURL 和 toBlob
                const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function(type, quality) {{
                    const tempCanvas = document.createElement('canvas');
                    tempCanvas.width = this.width;
                    tempCanvas.height = this.height;
                    const tempCtx = tempCanvas.getContext('2d');
                    tempCtx.drawImage(this, 0, 0);
                    
                    // 对每个像素的 RGB 加入微小偏移
                    const imageData = tempCtx.getImageData(0, 0, tempCanvas.width, tempCanvas.height);
                    const data = imageData.data;
                    for (let i = 0; i < data.length; i += 4) {{
                        // 只在部分像素加噪声以避免明显变化
                        if ((i / 4 + canvasSeed) % 7 === 0) {{
                            data[i] = Math.max(0, Math.min(255, data[i] + (Math.sin(canvasSeed + i) * noiseLevel)));
                            data[i+1] = Math.max(0, Math.min(255, data[i+1] + (Math.cos(canvasSeed + i + 1) * noiseLevel)));
                            data[i+2] = Math.max(0, Math.min(255, data[i+2] + (Math.sin(canvasSeed + i + 2) * noiseLevel)));
                        }}
                    }}
                    tempCtx.putImageData(imageData, 0, 0);
                    return origToDataURL.call(tempCanvas, type, quality);
                }};

                const origToBlob = HTMLCanvasElement.prototype.toBlob;
                HTMLCanvasElement.prototype.toBlob = function(callback, type, quality) {{
                    const dataUrl = this.toDataURL(type, quality);
                    const byteString = atob(dataUrl.split(',')[1]);
                    const mimeType = dataUrl.split(',')[0].split(':')[1].split(';')[0];
                    const ab = new ArrayBuffer(byteString.length);
                    const ia = new Uint8Array(ab);
                    for (let i = 0; i < byteString.length; i++) {{
                        ia[i] = byteString.charCodeAt(i);
                    }}
                    callback(new Blob([ab], {{type: mimeType}}));
                }};

                // ==========================================
                // 3. AudioContext 指纹欺骗
                // ==========================================
                const audioNoise = profile.audioNoiseLevel;
                const AudioCtx = window.AudioContext || window.webkitAudioContext;
                if (AudioCtx) {{
                    const origCreateOscillator = AudioCtx.prototype.createOscillator;
                    AudioCtx.prototype.createOscillator = function() {{
                        const osc = origCreateOscillator.call(this);
                        const origGetFrequencyResponse = osc.getFrequencyResponse;
                        osc.getFrequencyResponse = function(frequencyHz, magResponse, phaseResponse) {{
                            origGetFrequencyResponse.call(this, frequencyHz, magResponse, phaseResponse);
                            // 对幅度和相位加入微小噪声
                            for (let i = 0; i < magResponse.length; i++) {{
                                magResponse[i] += (Math.random() - 0.5) * audioNoise;
                            }}
                            for (let i = 0; i < phaseResponse.length; i++) {{
                                phaseResponse[i] += (Math.random() - 0.5) * audioNoise * 0.1;
                            }}
                        }};
                        return osc;
                    }};

                    const origCreateAnalyser = AudioCtx.prototype.createAnalyser;
                    AudioCtx.prototype.createAnalyser = function() {{
                        const analyser = origCreateAnalyser.call(this);
                        const origGetFloatFrequencyData = analyser.getFloatFrequencyData;
                        analyser.getFloatFrequencyData = function(array) {{
                            origGetFloatFrequencyData.call(this, array);
                            for (let i = 0; i < array.length; i++) {{
                                array[i] += (Math.random() - 0.5) * audioNoise * 10;
                            }}
                        }};
                        return analyser;
                    }};
                }}

                // ==========================================
                // 4. 字体检测欺骗
                // ==========================================
                // 覆盖 document.fonts 的行为
                if (document.fonts) {{
                    const fontSet = new Set(profile.fonts);
                    const origCheck = document.fonts.check;
                    document.fonts.check = function(font, text) {{
                        // 从 font 字符串提取字体族名称
                        const match = font.match(/"([^"]+)"|'([^']+)'|(?:,\\s*)?([^,]+)$/);
                        if (match) {{
                            const fontName = (match[1] || match[2] || match[3] || '').trim();
                            if (fontSet.has(fontName)) return true;
                        }}
                        return origCheck.call(this, font, text);
                    }};
                }}

                // ==========================================
                // 5. 覆盖 screen 和平台信息
                // ==========================================
                Object.defineProperties(window.screen, {{
                    colorDepth: {{ get: () => profile.colorDepth }},
                    pixelDepth: {{ get: () => profile.pixelDepth }},
                }});

                Object.defineProperty(navigator, 'platform', {{
                    get: () => profile.platform,
                }});

                // ==========================================
                // 6. Do Not Track
                // ==========================================
                if (profile.doNotTrack) {{
                    Object.defineProperty(navigator, 'doNotTrack', {{
                        get: () => profile.doNotTrack,
                    }});
                }}
            }})();
        """)


async def demo_fingerprint_spoofing():
    """演示指纹伪装效果。"""
    async with async_playwright() as p:
        # 先测试无 Stealth 的情况
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://bot.sannysoft.com", wait_until="networkidle")
        await page.screenshot(path="./screenshots/without_spoofing.png", full_page=True)

        # 再测试有指纹伪装的情况
        spoofer = FingerprintSpoofer(FingerprintProfile(
            webgl_vendor="Google Inc. (NVIDIA)",
            webgl_renderer="ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0)",
            platform="Win32",
        ))
        context2 = await browser.new_context()
        await spoofer.apply_to_context(context2)
        page2 = await context2.new_page()
        await page2.goto("https://bot.sannysoft.com", wait_until="networkidle")
        await page2.screenshot(path="./screenshots/with_spoofing.png", full_page=True)

        await browser.close()
        print("指纹伪装截图已保存，对比两张截图可见伪装效果。")


if __name__ == "__main__":
    asyncio.run(demo_fingerprint_spoofing())
```

---

## 5. 实战 Demo 3：人类行为模拟器

自动化工具的行为特征（鼠标轨迹完美直线、输入速度恒定、从不滚动等）是最容易被识别的。本 Demo 模拟人类的随机化操作模式。

```python
"""
human_behavior_simulator.py
人类行为模拟器 — 让自动化操作看起来像真人操作。
"""
import asyncio
import math
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from playwright.async_api import Page


@dataclass
class HumanBehaviorConfig:
    """人类行为模拟配置。"""
    # 鼠标移动
    mouse_move_min_steps: int = 8
    mouse_move_max_steps: int = 20
    mouse_move_min_delay_ms: int = 5
    mouse_move_max_delay_ms: int = 15
    
    # 点击行为
    click_before_delay_min_ms: int = 100    # 移动到目标后悬停时间
    click_before_delay_max_ms: int = 500
    click_after_delay_min_ms: int = 200     # 点击后等待时间
    click_after_delay_max_ms: int = 800
    
    # 输入行为
    typing_min_delay_ms: int = 50           # 每个字符的最小间隔
    typing_max_delay_ms: int = 200          # 每个字符的最大间隔
    typing_mistake_probability: float = 0.02  # 打错字概率 (2%)
    typing_correction_delay_min_ms: int = 500
    typing_correction_delay_max_ms: int = 1500
    
    # 滚动行为
    scroll_min_delay_ms: int = 500
    scroll_max_delay_ms: int = 3000
    scroll_min_distance: int = 100
    scroll_max_distance: int = 500
    scroll_segments_min: int = 3
    scroll_segments_max: int = 8
    
    # 页面浏览
    page_stay_min_seconds: float = 3.0
    page_stay_max_seconds: float = 15.0
    
    # 鼠标轨迹抖动
    jitter_amplitude: float = 3.0           # 贝塞尔曲线控制点偏移


class HumanBehaviorSimulator:
    """模拟人类在浏览器中的操作行为。"""

    def __init__(self, page: Page, config: Optional[HumanBehaviorConfig] = None):
        self.page = page
        self.config = config or HumanBehaviorConfig()

    # ==========================================
    # 1. 人类鼠标移动 — 贝塞尔曲线轨迹
    # ==========================================
    
    async def human_mouse_move(
        self,
        target_x: int,
        target_y: int,
        source_x: Optional[int] = None,
        source_y: Optional[int] = None,
    ) -> None:
        """
        模拟人类鼠标移动曲线（贝塞尔路径）。
        人类不会直线移动鼠标，而是带有弧度和微调。
        """
        # 获取当前鼠标位置
        if source_x is None or source_y is None:
            current_pos = await self.page.evaluate("({x: window.mouseX || 0, y: window.mouseY || 0})")
            source_x = current_pos["x"]
            source_y = current_pos["y"]

        # 生成贝塞尔曲线控制点
        control_points = self._generate_bezier_control_points(
            source_x, source_y, target_x, target_y
        )

        # 计算路径步数
        distance = math.sqrt((target_x - source_x) ** 2 + (target_y - source_y) ** 2)
        steps = max(
            self.config.mouse_move_min_steps,
            min(
                self.config.mouse_move_max_steps,
                int(distance / 15),  # 每 15px 一个步点
            )
        )

        # 沿贝塞尔曲线插值并移动鼠标
        for i in range(1, steps + 1):
            t = i / steps
            # 增加人类特有的"微调"抖动
            if 0.3 < t < 0.7:
                jitter_x = (random.random() - 0.5) * self.config.jitter_amplitude
                jitter_y = (random.random() - 0.5) * self.config.jitter_amplitude
            else:
                jitter_x = jitter_y = 0

            # 三次贝塞尔曲线插值
            px = self._cubic_bezier(
                source_x,
                control_points[0],
                control_points[1],
                target_x,
                t,
            ) + jitter_x
            py = self._cubic_bezier(
                source_y,
                control_points[2],
                control_points[3],
                target_y,
                t,
            ) + jitter_y

            await self.page.mouse.move(px, py)

            # 每步之间的延迟模拟人类肌肉运动的不均匀性
            delay = random.randint(
                self.config.mouse_move_min_delay_ms,
                self.config.mouse_move_max_delay_ms,
            )
            await asyncio.sleep(delay / 1000)

        # 最后精确移动到目标
        await self.page.mouse.move(target_x, target_y)

        # 更新存储的鼠标位置
        await self.page.evaluate(
            f"window.mouseX = {target_x}; window.mouseY = {target_y};"
        )

    def _generate_bezier_control_points(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
    ) -> tuple[float, float, float, float]:
        """生成使路径看起来自然的贝塞尔控制点。"""
        # 控制点偏移方向（倾向于"绕路"而不走直线）
        dx = x2 - x1
        dy = y2 - y1
        # 垂直于直线方向的偏移
        if abs(dx) < 1 and abs(dy) < 1:
            perp_x = 1
            perp_y = 0
        else:
            length = math.sqrt(dx * dx + dy * dy)
            perp_x = -dy / length
            perp_y = dx / length

        # 随机化控制点偏移量
        offset_magnitude = length * random.uniform(0.1, 0.4)
        offset_x = perp_x * offset_magnitude * random.choice([-1, 1])
        offset_y = perp_y * offset_magnitude * random.choice([-1, 1])

        cp1_x = x1 + dx * 0.3 + offset_x * random.uniform(0.5, 1.5)
        cp1_y = y1 + dy * 0.3 + offset_y * random.uniform(0.5, 1.5)
        cp2_x = x1 + dx * 0.7 + offset_x * random.uniform(0.5, 1.5)
        cp2_y = y1 + dy * 0.7 + offset_y * random.uniform(0.5, 1.5)

        return (cp1_x, cp1_y, cp2_x, cp2_y)

    def _cubic_bezier(
        self,
        p0: float,
        p1: float,
        p2: float,
        p3: float,
        t: float,
    ) -> float:
        """三次贝塞尔曲线插值。"""
        u = 1 - t
        return (
            u * u * u * p0
            + 3 * u * u * t * p1
            + 3 * u * t * t * p2
            + t * t * t * p3
        )

    # ==========================================
    # 2. 人类点击行为
    # ==========================================

    async def human_click(
        self,
        selector: str,
        force: bool = False,
    ) -> None:
        """模拟人类点击：移动到目标 → 悬停 → 点击 → 短暂等待。"""
        element = self.page.locator(selector)
        box = await element.bounding_box()
        if not box:
            raise ValueError(f"元素不可见: {selector}")

        # 点击目标坐标（随机偏移到元素内部，不是正中心）
        target_x = box["x"] + box["width"] * random.uniform(0.2, 0.8)
        target_y = box["y"] + box["height"] * random.uniform(0.2, 0.8)

        # 1. 人类移动鼠标到目标
        await self.human_mouse_move(target_x, target_y)

        # 2. 悬停 (人类在点击前会短暂停顿)
        hover_delay = random.randint(
            self.config.click_before_delay_min_ms,
            self.config.click_before_delay_max_ms,
        )
        await asyncio.sleep(hover_delay / 1000)

        # 3. 点击
        await self.page.mouse.click(target_x, target_y)

        # 4. 点击后短暂等待（人类点击后不会立即操作）
        after_delay = random.randint(
            self.config.click_after_delay_min_ms,
            self.config.click_after_delay_max_ms,
        )
        await asyncio.sleep(after_delay / 1000)

    # ==========================================
    # 3. 人类输入行为
    # ==========================================

    async def human_type(
        self,
        selector: str,
        text: str,
    ) -> None:
        """模拟人类键盘输入：每个字符有不同间隔，偶尔打错并修正。"""
        element = self.page.locator(selector)
        await element.click()

        # 清空已有内容 (人类会全选删除)
        await self.page.keyboard.press("Control+a")
        await asyncio.sleep(random.uniform(0.1, 0.3))
        await self.page.keyboard.press("Delete")
        await asyncio.sleep(random.uniform(0.2, 0.5))

        # 逐字符输入
        for i, char in enumerate(text):
            # 偶尔打错字（模拟打字错误）
            if (
                char.isalpha()
                and random.random() < self.config.typing_mistake_probability
            ):
                # 敲一个错误字符
                wrong_char = chr(ord(char) + random.choice([-1, 1]))
                await self.page.keyboard.press(wrong_char)
                await asyncio.sleep(random.uniform(0.1, 0.2))

                # "意识到"打错了，删除
                mistake_delay = random.randint(
                    self.config.typing_correction_delay_min_ms,
                    self.config.typing_correction_delay_max_ms,
                )
                await asyncio.sleep(mistake_delay / 1000)
                await self.page.keyboard.press("Backspace")
                await asyncio.sleep(random.uniform(0.1, 0.3))

            # 输入正确字符
            await self.page.keyboard.press(char)

            # 每个字符之间的延迟模拟人类的打字速度
            char_delay = random.randint(
                self.config.typing_min_delay_ms,
                self.config.typing_max_delay_ms,
            )
            await asyncio.sleep(char_delay / 1000)

            # 偶尔"停顿思考"
            if i > 0 and i % random.randint(8, 20) == 0:
                think_delay = random.uniform(0.3, 1.2)
                await asyncio.sleep(think_delay)

    # ==========================================
    # 4. 人类滚动行为
    # ==========================================

    async def human_scroll(
        self,
        direction: str = "down",
        distance: Optional[int] = None,
        target_selector: Optional[str] = None,
    ) -> None:
        """
        模拟人类滚动：不均匀速度、分段滚动、偶尔停顿阅读。
        
        Args:
            direction: "down" 或 "up"
            distance: 滚动总像素，默认随机 300-1500
            target_selector: 如果提供，滚动到该元素位置
        """
        if target_selector:
            # 获取目标元素位置
            element = self.page.locator(target_selector)
            box = await element.bounding_box()
            if not box:
                return
            # 分多次滚动到目标附近
            distance = int(box["y"] - 200)  # 留 200px 余量
            if distance <= 0:
                return

        if distance is None:
            distance = random.randint(
                self.config.scroll_min_distance,
                self.config.scroll_max_distance,
            )

        # 分段滚动（人类不会一滚到底）
        segments = random.randint(
            self.config.scroll_segments_min,
            self.config.scroll_segments_max,
        )
        segment_distance = distance // segments
        remaining = distance % segments

        current_scroll = 0
        for seg in range(segments):
            seg_dist = segment_distance + (remaining if seg == 0 else 0)
            
            # 每次滚动的速度不均匀
            scroll_speed = random.uniform(50, 150)  # px/步

            # 微滚动到该段目标
            for step in range(0, seg_dist, max(1, int(scroll_speed))):
                scroll_step = min(
                    int(scroll_speed * random.uniform(0.7, 1.3)),
                    seg_dist - step,
                )
                if direction == "down":
                    await self.page.evaluate(f"window.scrollBy(0, {scroll_step})")
                else:
                    await self.page.evaluate(f"window.scrollBy(0, -{scroll_step})")

                await asyncio.sleep(random.uniform(0.02, 0.08))

            current_scroll += seg_dist

            # 每段滚动后"停下来阅读"
            if seg < segments - 1:
                read_delay = random.uniform(0.5, 3.0)
                await asyncio.sleep(read_delay)

    # ==========================================
    # 5. 综合页面浏览
    # ==========================================

    async def browse_page_naturally(
        self,
        url: str,
        wait_for_selector: Optional[str] = None,
        scroll_probability: float = 0.8,
    ) -> None:
        """模拟人类自然浏览一个页面。"""
        await self.page.goto(url, wait_until="networkidle")

        # 页面加载后"停顿观察"
        await asyncio.sleep(random.uniform(0.5, 1.5))

        # 随机滚动浏览
        if random.random() < scroll_probability:
            await self.human_scroll("down", random.randint(500, 2000))

        # 等待指定的元素加载
        if wait_for_selector:
            await self.page.wait_for_selector(wait_for_selector, timeout=10000)

        # 随机"停留"一段时间
        stay_time = random.uniform(
            self.config.page_stay_min_seconds,
            self.config.page_stay_max_seconds,
        )
        # 停留期间产生一些随机活动（模拟人还在看页面）
        await self._idle_activity(stay_time)

    async def _idle_activity(self, duration_seconds: float) -> None:
        """模拟浏览页面时的小动作。"""
        start = time.time()
        while time.time() - start < duration_seconds:
            activity = random.choice([
                "scroll_small",
                "move_mouse",
                "do_nothing",
                "do_nothing",
                "do_nothing",
            ])
            if activity == "scroll_small":
                await self.page.evaluate(
                    f"window.scrollBy(0, {random.randint(-50, 50)})"
                )
                await asyncio.sleep(random.uniform(0.3, 1.0))
            elif activity == "move_mouse":
                current_pos = await self.page.evaluate(
                    "({x: window.mouseX || 0, y: window.mouseY || 0})"
                )
                await self.human_mouse_move(
                    current_pos["x"] + random.randint(-30, 30),
                    current_pos["y"] + random.randint(-30, 30),
                )
            else:
                await asyncio.sleep(random.uniform(0.5, 2.0))


# ===== 使用示例 =====
async def demo_human_behavior():
    """演示人类行为模拟。"""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()

        human = HumanBehaviorSimulator(page)

        # 自然浏览一个页面
        await human.browse_page_naturally(
            "https://quotes.toscrape.com",
            scroll_probability=0.9,
        )

        # 模拟人类点击下一页
        await human.human_click(".next a")

        # 模拟人类搜索/输入
        await asyncio.sleep(1)
        await human.human_type("input[type='text']", "love" if False else "")

        await asyncio.sleep(3)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(demo_human_behavior())
```

---

## 6. 实战 Demo 4：动态代理与 IP 轮换

频繁的 IP 请求从同一 IP 发出是自动化被检测的主要原因之一。本 Demo 实现 IP 轮换和请求特征伪装。

```python
"""
proxy_rotator.py
动态代理轮换与请求特征伪装引擎。
"""
import asyncio
import logging
import random
from dataclasses import dataclass, field
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Route, async_playwright

logger = logging.getLogger("ProxyRotator")


@dataclass
class ProxyConfig:
    """代理配置。"""
    proxies: list[dict] = field(default_factory=lambda: [
        # 格式: {"server": "http://proxy1:8080", "username": "user", "password": "pass"}
        # 使用 HTTP/HTTPS/SOCKS5 代理
    ])
    rotate_every_n_requests: int = 10  # 每 N 个请求轮换一次代理
    current_index: int = 0
    request_count: int = 0


class RequestHeaderSpoofer:
    """
    请求头伪装器。
    真实浏览器的请求头顺序和特征与 Playwright 默认不同。
    这里不修改请求头内容（那是反检测），而是确保请求头顺序和特征一致。
    """

    @staticmethod
    def get_custom_headers() -> dict[str, str]:
        """返回一组看起来像真实浏览器的自定义请求头。"""
        return {
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
            ),
            "Sec-Ch-Ua": (
                '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"'
            ),
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Dnt": "1",
        }


class ProxyRotator:
    """动态代理轮换引擎。"""

    def __init__(
        self,
        config: Optional[ProxyConfig] = None,
        user_agent_rotation: bool = True,
    ):
        self.config = config or ProxyConfig()
        self.user_agent_rotation = user_agent_rotation
        
        # 常见的 User-Agent 池（按系统分）
        self.user_agent_pool: dict[str, list[str]] = {
            "windows": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
            ],
            "macos": [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
            ],
            "linux": [
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            ],
        }

    def get_next_proxy(self) -> Optional[dict]:
        """获取下一个代理配置。"""
        if not self.config.proxies:
            return None
        proxy = self.config.proxies[self.config.current_index]
        self.config.request_count += 1
        if self.config.request_count % self.config.rotate_every_n_requests == 0:
            self.config.current_index = (self.config.current_index + 1) % len(
                self.config.proxies
            )
        return proxy

    def get_random_user_agent(self, platform: str = "windows") -> str:
        """从池中随机选择一个 User-Agent。"""
        agents = self.user_agent_pool.get(platform, self.user_agent_pool["windows"])
        return random.choice(agents)

    async def create_stealth_context_with_proxy(
        self,
        browser: Browser,
        platform: str = "windows",
    ) -> BrowserContext:
        """创建一个带有随机代理和 User-Agent 的上下文。"""
        proxy = self.get_next_proxy()
        ua = self.get_random_user_agent(platform)

        context_options = {
            "user_agent": ua,
            "viewport": {"width": 1920, "height": 1080},
            "locale": random.choice(["zh-CN", "en-US", "en-GB", "ja-JP"]),
        }

        if proxy:
            context_options["proxy"] = proxy

        context = await browser.new_context(**context_options)

        # 添加请求头伪装
        headers = RequestHeaderSpoofer.get_custom_headers()
        await context.set_extra_http_headers(headers)

        # 注入 Stealth 脚本
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)

        return context


# ===== 使用示例 =====
async def demo_proxy_rotation():
    """演示代理轮换。"""
    config = ProxyConfig(
        proxies=[
            # 实际使用时替换为真实代理
            # {"server": "http://proxy1.example.com:8080"},
            # {"server": "http://proxy2.example.com:8080"},
        ],
        rotate_every_n_requests=5,
    )
    rotator = ProxyRotator(config)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        context = await rotator.create_stealth_context_with_proxy(browser)
        page = await context.new_page()
        
        await page.goto("https://httpbin.org/ip", wait_until="networkidle")
        ip_info = await page.text_content("body")
        logger.info("当前 IP: %s", ip_info)
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(demo_proxy_rotation())
```

---

## 7. 实战 Demo 5：自动化检测页面综合测试

这是一个"自检"工具，帮助你评估当前的 Stealth 配置是否有效。

```python
"""
stealth_checker.py
Stealth 效果检测器 — 在多个检测页面测试浏览器伪装效果。
"""
import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

logger = logging.getLogger("StealthChecker")


@dataclass
class StealthTestResult:
    """单项 Stealth 测试结果。"""
    name: str
    passed: bool
    details: str
    evidence: Optional[dict[str, Any]] = None


@dataclass
class StealthTestReport:
    """完整的 Stealth 测试报告。"""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    results: list[StealthTestResult] = field(default_factory=list)
    score: float = 0.0
    
    def add_result(self, result: StealthTestResult) -> None:
        self.results.append(result)
        self.total_tests += 1
        if result.passed:
            self.passed += 1
        else:
            self.failed += 1
        self.score = (self.passed / self.total_tests * 100) if self.total_tests > 0 else 0
    
    def summarize(self) -> str:
        return (
            f"=== Stealth 测试报告 ===\n"
            f"总分: {self.score:.1f}% ({self.passed}/{self.total_tests})\n"
            f"通过: {self.passed} | 失败: {self.failed}\n"
        )
    
    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "passed": self.passed,
            "failed": self.failed,
            "total": self.total_tests,
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "details": r.details,
                }
                for r in self.results
            ],
        }


class StealthChecker:
    """
    Stealth 效果检测器。
    在内置检测页面上运行一系列测试，评估当前浏览器配置的隐身效果。
    """

    def __init__(self, page: Page):
        self.page = page
        self.report = StealthTestReport()

    async def run_all_tests(self) -> StealthTestReport:
        """运行所有检测项目。"""
        test_methods = [
            self.test_webdriver_flag,
            self.test_plugins,
            self.test_languages,
            self.test_chrome_object,
            self.test_webgl_fingerprint,
            self.test_canvas_fingerprint,
            self.test_hardware_concurrency,
            self.test_device_memory,
            self.test_platform,
            self.test_user_agent,
            self.test_permissions,
            self.test_screen_properties,
            self.test_fonts,
        ]
        
        for test_method in test_methods:
            try:
                result = await test_method()
                self.report.add_result(result)
            except Exception as e:
                self.report.add_result(StealthTestResult(
                    name=test_method.__name__,
                    passed=False,
                    details=f"测试执行异常: {e}",
                ))
        
        return self.report

    async def test_webdriver_flag(self) -> StealthTestResult:
        """测试 navigator.webdriver 是否被隐藏。"""
        webdriver = await self.page.evaluate("navigator.webdriver")
        passed = webdriver is None or webdriver is False or webdriver == "undefined"
        return StealthTestResult(
            name="navigator.webdriver",
            passed=passed,
            details=f"值 = {webdriver!r} (期望: undefined 或 false)",
        )

    async def test_plugins(self) -> StealthTestResult:
        """测试 navigator.plugins.length 是否有模拟值。"""
        plugins_len = await self.page.evaluate("navigator.plugins.length")
        plugins_info = await self.page.evaluate("""
            Array.from(navigator.plugins).map(p => ({
                name: p.name,
                description: p.description,
            }))
        """)
        passed = plugins_len > 0
        return StealthTestResult(
            name="navigator.plugins",
            passed=passed,
            details=f"插件数量 = {plugins_len}, 详情 = {json.dumps(plugins_info, ensure_ascii=False)}",
        )

    async def test_languages(self) -> StealthTestResult:
        """测试 navigator.languages 是否合理。"""
        languages = await self.page.evaluate("navigator.languages")
        passed = len(languages) >= 2
        return StealthTestResult(
            name="navigator.languages",
            passed=passed,
            details=f"languages = {languages}",
        )

    async def test_chrome_object(self) -> StealthTestResult:
        """测试 window.chrome 对象是否存在且完整。"""
        chrome_info = await self.page.evaluate("""
            ({
                exists: typeof window.chrome !== 'undefined',
                hasRuntime: typeof window.chrome.runtime !== 'undefined',
                hasLoadTimes: typeof window.chrome.loadTimes === 'function',
                hasCsi: typeof window.chrome.csi === 'function',
                hasApp: typeof window.chrome.app !== 'undefined',
            })
        """)
        passed = all(chrome_info.values())
        return StealthTestResult(
            name="window.chrome",
            passed=passed,
            details=json.dumps(chrome_info),
        )

    async def test_webgl_fingerprint(self) -> StealthTestResult:
        """测试 WebGL 信息是否被伪装。"""
        webgl_info = await self.page.evaluate("""
            () => {
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                if (!gl) return {error: 'WebGL not supported'};
                return {
                    vendor: gl.getParameter(gl.VENDOR),
                    renderer: gl.getParameter(gl.RENDERER),
                    unmaskedVendor: gl.getExtension('WEBGL_debug_renderer_info')
                        ?.UNMASKED_VENDOR_WEBGL,
                    unmaskedRenderer: gl.getExtension('WEBGL_debug_renderer_info')
                        ?.UNMASKED_RENDERER_WEBGL,
                };
            }
        """)
        # 检查是否包含 "SwiftShader" 或 "Google" 等无头特征
        renderer = (webgl_info.get("renderer") or "").lower()
        has_swiftshader = "swiftshader" in renderer
        passed = not has_swiftshader
        return StealthTestResult(
            name="WebGL 指纹",
            passed=passed,
            details=json.dumps(webgl_info, ensure_ascii=False),
        )

    async def test_canvas_fingerprint(self) -> StealthTestResult:
        """测试 Canvas 指纹是否被添加噪声。"""
        canvas_hash = await self.page.evaluate("""
            () => {
                const canvas = document.createElement('canvas');
                canvas.width = 200;
                canvas.height = 50;
                const ctx = canvas.getContext('2d');
                ctx.textBaseline = 'top';
                ctx.font = '14px Arial';
                ctx.fillStyle = '#f60';
                ctx.fillRect(125, 1, 62, 20);
                ctx.fillStyle = '#069';
                ctx.fillText('Stealth Test', 2, 15);
                return canvas.toDataURL();
            }
        """)
        # 检查数据 URL 是否有实际内容
        passed = canvas_hash.startswith("data:image/png") and len(canvas_hash) > 100
        return StealthTestResult(
            name="Canvas 指纹",
            passed=passed,
            details=f"Canvas Hash 长度: {len(canvas_hash)}",
            evidence={"hash_prefix": canvas_hash[:50] + "..."},
        )

    async def test_hardware_concurrency(self) -> StealthTestResult:
        """测试 hardwareConcurrency 的值是否合理。"""
        hc = await self.page.evaluate("navigator.hardwareConcurrency")
        passed = hc >= 2 and hc <= 64
        return StealthTestResult(
            name="navigator.hardwareConcurrency",
            passed=passed,
            details=f"CPU 核心数 = {hc}",
        )

    async def test_device_memory(self) -> StealthTestResult:
        """测试 deviceMemory 的值是否合理。"""
        dm = await self.page.evaluate("navigator.deviceMemory")
        passed = dm >= 2 and dm <= 64
        return StealthTestResult(
            name="navigator.deviceMemory",
            passed=passed,
            details=f"设备内存 = {dm} GB",
        )

    async def test_platform(self) -> StealthTestResult:
        """测试 navigator.platform 的值是否合理。"""
        platform = await self.page.evaluate("navigator.platform")
        passed = platform in ("Win32", "MacIntel", "Linux x86_64", "Linux armv8l")
        return StealthTestResult(
            name="navigator.platform",
            passed=passed,
            details=f"platform = {platform}",
        )

    async def test_user_agent(self) -> StealthTestResult:
        """测试 User-Agent 是否合理。"""
        ua = await self.page.evaluate("navigator.userAgent")
        has_browser_keywords = any(
            kw in ua for kw in ["Chrome", "Firefox", "Safari", "Edg"]
        )
        has_headless_keywords = "Headless" in ua
        passed = has_browser_keywords and not has_headless_keywords
        return StealthTestResult(
            name="User-Agent",
            passed=passed,
            details=f"UA = {ua}\n  含 Headless 标记: {has_headless_keywords}",
        )

    async def test_permissions(self) -> StealthTestResult:
        """测试权限 API 是否行为正常。"""
        perm_info = await self.page.evaluate("""
            async () => {
                const results = {};
                for (const name of ['geolocation', 'notifications', 'microphone', 'camera']) {
                    try {
                        const status = await navigator.permissions.query({name});
                        results[name] = status.state;
                    } catch(e) {
                        results[name] = 'error: ' + e.message;
                    }
                }
                return results;
            }
        """)
        passed = perm_info.get("geolocation") != "denied"
        return StealthTestResult(
            name="Permissions API",
            passed=passed,
            details=f"权限状态: {json.dumps(perm_info, ensure_ascii=False)}",
        )

    async def test_screen_properties(self) -> StealthTestResult:
        """测试 screen 属性是否合理。"""
        screen_info = await self.page.evaluate("""
            ({
                width: screen.width,
                height: screen.height,
                colorDepth: screen.colorDepth,
                pixelDepth: screen.pixelDepth,
                availWidth: screen.availWidth,
                availHeight: screen.availHeight,
            })
        """)
        passed = (
            screen_info["colorDepth"] >= 24
            and screen_info["width"] >= 1024
        )
        return StealthTestResult(
            name="Screen 属性",
            passed=passed,
            details=json.dumps(screen_info),
        )

    async def test_fonts(self) -> StealthTestResult:
        """测试页面可检测到的字体数量。"""
        fonts_count = await self.page.evaluate("""
            () => {
                const baseFonts = ['monospace', 'sans-serif', 'serif'];
                const testString = 'mmmmmmmmmmlli';
                const testSize = '72px';
                const testEl = document.createElement('div');
                testEl.style.cssText = `position:absolute;left:-9999px;font-size:${testSize};`;
                document.body.appendChild(testEl);
                
                const baseWidths = {};
                for (const base of baseFonts) {
                    testEl.style.fontFamily = base;
                    baseWidths[base] = testEl.offsetWidth;
                }
                
                const fontList = [
                    'Arial','Helvetica','Times New Roman','Courier New','Verdana',
                    'Georgia','Palatino Linotype','Tahoma','Trebuchet MS',
                    'Microsoft YaHei','SimSun','SimHei',
                ];
                let detected = 0;
                for (const font of fontList) {
                    let detected_any = false;
                    for (const base of baseFonts) {
                        testEl.style.fontFamily = `"${font}",${base}`;
                        if (testEl.offsetWidth !== baseWidths[base]) {
                            detected_any = true;
                            break;
                        }
                    }
                    if (detected_any) detected++;
                }
                document.body.removeChild(testEl);
                return detected;
            }
        """)
        passed = fonts_count >= 3
        return StealthTestResult(
            name="系统字体检测",
            passed=passed,
            details=f"检测到 {fonts_count} 种字体 (超过 3 种即正常)",
        )


# ===== 直接使用检测页面 =====
async def run_stealth_self_check(
    screenshot_dir: str = "./screenshots",
) -> StealthTestReport:
    """在多个知名检测站点上测试 Stealth 配置。"""
    output_dir = Path(screenshot_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    from stealth_browser_factory import StealthBrowserFactory, StealthConfig

    config = StealthConfig(headless=True)
    factory = StealthBrowserFactory(config)
    browser = await factory.create_browser()
    context = await factory.create_stealth_context(browser)
    page = await factory.create_page(context)

    checker = StealthChecker(page)
    
    # 检测站点列表
    test_sites = [
        {
            "url": "https://bot.sannysoft.com",
            "name": "SannySoft Bot Detector",
            "screenshot": "sannysoft.png",
        },
        {
            "url": "https://fingerprintjs.github.io/fingerprintjs/",
            "name": "FingerprintJS",
            "screenshot": "fingerprintjs.png",
            "wait_for": ".content",
        },
        {
            "url": "https://abrahamjuliot.github.io/creepjs/",
            "name": "CreepJS",
            "screenshot": "creepjs.png",
            "wait_for": "body",
        },
        {
            "url": "https://amiunique.org/fp",
            "name": "AmIUnique",
            "screenshot": "amiunique.png",
            "wait_for": "body",
        },
    ]

    print("=" * 60)
    print("Stealth 自检报告")
    print("=" * 60)

    # 在本地运行特征测试
    await page.goto("about:blank")
    report = await checker.run_all_tests()
    print(report.summarize())
    for r in report.results:
        status = "✅" if r.passed else "❌"
        print(f"  {status} {r.name:<35s} | {r.details[:80]}")

    # 截图检测站点
    print("\n访问检测站点中...")
    for site in test_sites:
        try:
            await page.goto(site["url"], wait_until="domcontentloaded", timeout=30000)
            if site.get("wait_for"):
                try:
                    await page.wait_for_selector(
                        site["wait_for"], timeout=10000
                    )
                except Exception:
                    pass
            await asyncio.sleep(2)  # 等待指纹JS加载
            await page.screenshot(
                path=str(output_dir / site["screenshot"]),
                full_page=True,
            )
            print(f"  ✅ {site['name']:<35s} 截图已保存")
        except Exception as e:
            print(f"  ❌ {site['name']:<35s} 访问失败: {e}")

    await browser.close()
    
    # 保存报告
    report_path = output_dir / "stealth_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"\n报告已保存至: {report_path}")
    
    return report


async def demo_stealth_check():
    """运行 Stealth 自检。"""
    report = await run_stealth_self_check()
    print(f"\n最终评分: {report.score:.1f}%")
    print(f"建议: ", end="")
    if report.score >= 90:
        print("你的 Stealth 配置很强 🔥")
    elif report.score >= 70:
        print("基本可用，建议提升薄弱项 ⚠️")
    else:
        print("需要大幅加强 Stealth 配置 🚨")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(demo_stealth_check())
```

---

## 8. 实战 Demo 6：生产级 Stealth Agent 框架

综合所有技术，构建一个可直接用于生产环境的 Stealth Agent 框架。

```python
"""
stealth_agent.py
生产级 Stealth Agent 框架 — 一站式解决浏览器自动化 + 反检测。
"""
import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Response,
    Route,
    async_playwright,
)

logger = logging.getLogger("StealthAgent")


class TaskType(Enum):
    """任务类型枚举。"""
    DATA_EXTRACTION = "data_extraction"
    FORM_FILLING = "form_filling"
    MONITORING = "monitoring"
    SOCIAL_MEDIA = "social_media"
    ECOMMERCE = "ecommerce"
    CUSTOM = "custom"


@dataclass
class StealthAgentConfig:
    """Stealth Agent 综合配置。"""
    # 浏览器配置
    headless: bool = True
    browser_type: str = "chromium"  # chromium | firefox | webkit
    
    # 窗口配置
    viewport_width: int = 1920
    viewport_height: int = 1080
    device_scale_factor: float = 1.0
    
    # 地区配置
    locale: str = "zh-CN"
    timezone_id: str = "Asia/Shanghai"
    geolocation: dict = field(default_factory=lambda: {
        "latitude": 39.9042,
        "longitude": 116.4074,
    })
    
    # User-Agent 配置
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
    
    # 代理配置
    proxy: Optional[dict] = None
    
    # 人类行为模拟开关
    enable_human_behavior: bool = True
    
    # 指纹伪装开关
    enable_fingerprint_spoofing: bool = True
    
    # 请求头伪装开关
    enable_header_spoofing: bool = True
    
    # Cookie/会话持久化
    session_storage_dir: str = "./sessions"
    
    # 截图目录
    screenshot_dir: str = "./screenshots"
    
    # 请求控制
    max_retries: int = 3
    retry_delay_seconds: float = 2.0
    request_timeout_ms: int = 30000
    
    # 速率限制
    min_delay_between_requests: float = 1.0
    max_delay_between_requests: float = 3.0
    
    # 启动参数
    launch_args: list[str] = field(default_factory=lambda: [
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-web-security",
        "--disable-infobars",
        "--window-size=1920,1080",
        "--start-maximized",
    ])


class StealthAgent:
    """
    生产级 Stealth Agent。
    结合浏览器自动化、反检测、人类行为模拟、会话管理于一体的完整框架。
    """

    def __init__(self, config: Optional[StealthAgentConfig] = None):
        self.config = config or StealthAgentConfig()
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._session_name: Optional[str] = None
        
        # 建立目录
        Path(self.config.screenshot_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.session_storage_dir).mkdir(parents=True, exist_ok=True)

    # ==========================================
    # 生命周期管理
    # ==========================================

    async def start(
        self,
        session_name: Optional[str] = None,
    ) -> None:
        """启动 Stealth Agent（浏览器 + 上下文 + 页面）。"""
        logger.info("🚀 Stealth Agent 启动中...")
        
        self._playwright = await async_playwright().start()
        self._session_name = session_name

        # 1. 启动浏览器
        browser_launcher = getattr(self._playwright, self.config.browser_type)
        self._browser = await browser_launcher.launch(
            headless=self.config.headless,
            args=self.config.launch_args,
        )
        logger.info("✅ 浏览器已启动 (headless=%s)", self.config.headless)

        # 2. 创建上下文
        if session_name and self._session_file_exists(session_name):
            self._context = await self._load_session_context(session_name)
            logger.info("✅ 已恢复会话: %s", session_name)
        else:
            self._context = await self._create_stealth_context()
            logger.info("✅ 已创建新会话")

        # 3. 创建页面
        self._page = await self._context.new_page()
        
        # 4. 设置事件监听
        self._setup_listeners()

        logger.info("🎯 Stealth Agent 准备就绪")

    async def stop(self) -> None:
        """停止 Agent，保存会话并关闭浏览器。"""
        # 保存会话
        if self._session_name and self._context:
            await self._save_session(self._session_name)
            logger.info("💾 会话已保存: %s", self._session_name)

        # 关闭浏览器
        if self._browser:
            await self._browser.close()
            logger.info("🛑 浏览器已关闭")

        # 停止 Playwright
        if self._playwright:
            await self._playwright.stop()

        self._browser = None
        self._context = None
        self._page = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.stop()

    # ==========================================
    # 核心操作方法（带人类行为模拟）
    # ==========================================

    async def navigate(self, url: str, **kwargs) -> Optional[Response]:
        """导航到 URL（带重试和延迟）。"""
        for attempt in range(1, self.config.max_retries + 1):
            try:
                response = await self.page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=self.config.request_timeout_ms,
                    **kwargs,
                )
                
                # 模拟人类浏览：页面加载后"停顿"
                if self.config.enable_human_behavior:
                    await asyncio.sleep(random.uniform(0.5, 2.0))
                
                return response
            except Exception as e:
                logger.warning("⏳ 导航失败 (尝试 %d/%d): %s", attempt, self.config.max_retries, e)
                if attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay_seconds * attempt)
                else:
                    raise

    async def click(self, selector: str, **kwargs) -> None:
        """点击元素（使用人类行为模拟或直接点击）。"""
        if self.config.enable_human_behavior:
            # 导入 HumanBehaviorSimulator 的方法
            await self._human_click(selector)
        else:
            await self.page.locator(selector).click(**kwargs)

    async def fill(self, selector: str, text: str) -> None:
        """填写输入框（使用人类行为模拟或直接填入）。"""
        if self.config.enable_human_behavior:
            await self._human_type(selector, text)
        else:
            await self.page.locator(selector).fill(text)

    async def extract_text(self, selector: str) -> str:
        """提取元素文本。"""
        element = self.page.locator(selector)
        if await element.count() > 0:
            return await element.inner_text()
        return ""

    async def extract_all_texts(self, selector: str) -> list[str]:
        """提取所有匹配元素的文本。"""
        return await self.page.locator(selector).all_inner_texts()

    async def extract_attribute(self, selector: str, attribute: str) -> list[str]:
        """提取元素属性。"""
        return await self.page.locator(selector).evaluate_all(
            f"els => els.map(el => el.getAttribute('{attribute}'))"
        )

    async def scroll_down(self, distance: Optional[int] = None) -> None:
        """向下滚动页面。"""
        if self.config.enable_human_behavior:
            await self._human_scroll("down", distance)
        else:
            if distance:
                await self.page.evaluate(f"window.scrollBy(0, {distance})")
            else:
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    async def screenshot(self, name: str, full_page: bool = True) -> Path:
        """截取页面截图。"""
        filepath = Path(self.config.screenshot_dir) / name
        await self.page.screenshot(path=str(filepath), full_page=full_page)
        return filepath

    async def wait_and_click(self, selector: str, timeout: int = 10000) -> bool:
        """等待元素出现后点击。"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            await self.click(selector)
            return True
        except Exception:
            return False

    # ==========================================
    # 会话管理
    # ==========================================

    def _session_file_exists(self, name: str) -> bool:
        return (Path(self.config.session_storage_dir) / f"{name}.json").exists()

    async def _save_session(self, name: str) -> None:
        """保存当前会话状态。"""
        if not self._context:
            return
        state = await self._context.storage_state()
        filepath = Path(self.config.session_storage_dir) / f"{name}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    async def _load_session_context(self, name: str) -> BrowserContext:
        """从保存的状态恢复浏览器上下文。"""
        filepath = Path(self.config.session_storage_dir) / f"{name}.json"
        with open(filepath, "r", encoding="utf-8") as f:
            state = json.load(f)
        context = await self._browser.new_context(storage_state=state)
        await self._inject_stealth_scripts(context)
        return context

    # ==========================================
    # Stealth 注入
    # ==========================================

    async def _create_stealth_context(self) -> BrowserContext:
        """创建带有全面 Stealth 配置的浏览器上下文。"""
        context_options = {
            "viewport": {
                "width": self.config.viewport_width,
                "height": self.config.viewport_height,
            },
            "device_scale_factor": self.config.device_scale_factor,
            "user_agent": self.config.user_agent,
            "locale": self.config.locale,
            "timezone_id": self.config.timezone_id,
            "permissions": ["geolocation", "notifications"],
            "geolocation": self.config.geolocation,
        }

        if self.config.proxy:
            context_options["proxy"] = self.config.proxy

        context = await self._browser.new_context(**context_options)

        # 注入 Stealth 脚本
        await self._inject_stealth_scripts(context)

        # 设置请求头
        if self.config.enable_header_spoofing:
            await context.set_extra_http_headers({
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
                ),
                "Sec-Ch-Ua": (
                    '"Google Chrome";v="125", "Chromium";v="125", '
                    '"Not.A/Brand";v="24"'
                ),
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Upgrade-Insecure-Requests": "1",
            })

        return context

    async def _inject_stealth_scripts(self, context: BrowserContext) -> None:
        """注入所有 Stealth JavaScript 脚本。"""
        await context.add_init_script("""
            (() => {
                // 1. webdriver
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                // 2. plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        { name: "Chrome PDF Plugin", description: "Portable Document Format", filename: "internal-pdf-viewer", length: 1 },
                        { name: "Chrome PDF Viewer", description: "", filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai", length: 1 },
                        { name: "Native Client", description: "Native Client Executable", filename: "internal-nacl-plugin", length: 2 },
                    ],
                });

                // 3. languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en'],
                });

                // 4. chrome object
                window.chrome = {
                    runtime: { onConnect: { addListener: function(){} }, onMessage: { addListener: function(){} } },
                    loadTimes: function() { return {}; },
                    csi: function() { return {}; },
                    app: { isInstalled: false },
                    webstore: { onInstallStageChanged: { addListener: function(){} }, onDownloadProgress: { addListener: function(){} } },
                    runtimeOnConnect: { addListener: function(){} },
                };

                // 5. hardware concurrency
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 8,
                });

                // 6. device memory
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8,
                });

                // 7. WebGL
                try {
                    const canvas = document.createElement('canvas');
                    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    if (gl) {
                        const origGetParam = gl.getParameter.bind(gl);
                        gl.getParameter = function(param) {
                            const map = {
                                37445: "INTEL INC.",
                                37446: "INTEL Iris OpenGL Engine",
                                7936: "WebKit WebGL",
                                7937: "OpenGL ES 2.0 (ANGLE 2.1.0.24506)",
                            };
                            return param in map ? map[param] : origGetParam(param);
                        };
                    }
                } catch(e) {}

                // 8. permissions override
                const origQuery = navigator.permissions.query.bind(navigator.permissions);
                navigator.permissions.query = (params) => {
                    if (params.name === 'notifications') {
                        return Promise.resolve({ state: 'prompt', onchange: null });
                    }
                    return origQuery(params);
                };

                // 9. screen
                Object.defineProperties(screen, {
                    colorDepth: { get: () => 24 },
                    pixelDepth: { get: () => 24 },
                });

                // 10. platform
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32',
                });
            })();
        """)

    # ==========================================
    # 事件监听器
    # ==========================================

    def _setup_listeners(self) -> None:
        """设置页面事件监听器。"""
        if not self._page:
            return

        # 请求失败监听
        self._page.on("requestfailed", lambda req: logger.debug(
            "请求失败: %s %s", req.method, req.url
        ))

        # 响应监听（记录异常状态码）
        self._page.on("response", lambda resp: logger.debug(
            "响应: %d %s", resp.status, resp.url
        ) if resp.status >= 400 else None)

        # 控制台消息监听
        self._page.on("console", lambda msg: logger.debug(
            "控制台 %s: %s", msg.type, msg.text
        ) if msg.type == "error" else None)

    # ==========================================
    # 人类行为模拟（内部方法）
    # ==========================================

    async def _human_click(self, selector: str) -> None:
        """模拟人类点击。"""
        element = self.page.locator(selector)
        box = await element.bounding_box()
        if not box:
            raise ValueError(f"元素不可见: {selector}")

        target_x = box["x"] + box["width"] * random.uniform(0.2, 0.8)
        target_y = box["y"] + box["height"] * random.uniform(0.2, 0.8)

        # 获取当前鼠标位置
        current = await self.page.evaluate(
            "({x: window._lastMouseX || 0, y: window._lastMouseY || 0})"
        )

        # 贝塞尔曲线移动
        steps = random.randint(8, 15)
        for i in range(1, steps + 1):
            t = i / steps
            px = self._cubic_bezier(current["x"], current["x"] + random.randint(-30, 30),
                                     target_x + random.randint(-30, 30), target_x, t)
            py = self._cubic_bezier(current["y"], current["y"] + random.randint(-30, 30),
                                     target_y + random.randint(-30, 30), target_y, t)
            await self.page.mouse.move(px, py)
            await asyncio.sleep(random.uniform(0.005, 0.015))

        # 悬停
        await asyncio.sleep(random.uniform(0.1, 0.4))

        # 点击
        await self.page.mouse.click(target_x, target_y)
        await self.page.evaluate(
            f"window._lastMouseX = {target_x}; window._lastMouseY = {target_y};"
        )
        await asyncio.sleep(random.uniform(0.2, 0.5))

    async def _human_type(self, selector: str, text: str) -> None:
        """模拟人类输入。"""
        element = self.page.locator(selector)
        await element.click()
        await asyncio.sleep(random.uniform(0.1, 0.3))

        # 清空
        await self.page.keyboard.press("Control+a")
        await asyncio.sleep(random.uniform(0.1, 0.2))
        await self.page.keyboard.press("Delete")
        await asyncio.sleep(random.uniform(0.2, 0.4))

        # 逐字符输入
        for char in text:
            await self.page.keyboard.press(char)
            await asyncio.sleep(random.uniform(0.05, 0.15))

    async def _human_scroll(self, direction: str = "down", distance: Optional[int] = None) -> None:
        """模拟人类滚动。"""
        if distance is None:
            distance = random.randint(300, 1000)

        segments = random.randint(3, 6)
        seg_dist = distance // segments

        for _ in range(segments):
            for step in range(0, seg_dist, random.randint(30, 80)):
                scroll_by = random.randint(20, 50)
                if direction == "up":
                    scroll_by = -scroll_by
                await self.page.evaluate(f"window.scrollBy(0, {scroll_by})")
                await asyncio.sleep(random.uniform(0.01, 0.05))
            await asyncio.sleep(random.uniform(0.5, 2.0))

    def _cubic_bezier(self, p0: float, p1: float, p2: float, p3: float, t: float) -> float:
        """三次贝塞尔曲线。"""
        u = 1 - t
        return u * u * u * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t * t * t * p3

    # ==========================================
    # 属性访问
    # ==========================================

    @property
    def page(self) -> Page:
        if not self._page:
            raise RuntimeError("Agent 尚未启动，请先调用 start()")
        return self._page

    @property
    def context(self) -> BrowserContext:
        if not self._context:
            raise RuntimeError("Agent 尚未启动，请先调用 start()")
        return self._context

    @property
    def browser(self) -> Browser:
        if not self._browser:
            raise RuntimeError("Agent 尚未启动，请先调用 start()")
        return self._browser

    @property
    def is_running(self) -> bool:
        return self._page is not None


# ==========================================
# 使用示例
# ==========================================

async def demo_collect_quotes():
    """演示：使用 Stealth Agent 采集引文数据。"""
    config = StealthAgentConfig(
        headless=True,
        enable_human_behavior=True,
        enable_fingerprint_spoofing=True,
        session_storage_dir="./sessions",
        screenshot_dir="./screenshots",
    )

    async with StealthAgent(config) as agent:
        # 导航到目标页面
        await agent.navigate("https://quotes.toscrape.com")
        await agent.screenshot("quotes_page.png")

        all_quotes = []
        page_num = 1

        while page_num <= 3:
            logger.info("📄 采集第 %d 页...", page_num)

            # 提取当前页数据
            quotes = await agent.extract_all_texts(".quote .text")
            authors = await agent.extract_all_texts(".quote .author")
            tags_lists = await agent.extract_attribute(".quote .tag", "class")

            for i in range(len(quotes)):
                all_quotes.append({
                    "text": quotes[i] if i < len(quotes) else "",
                    "author": authors[i] if i < len(authors) else "",
                })

            # 翻页
            has_next = await agent.extract_text(".next a")
            if not has_next:
                break

            # 人类行为翻页
            if agent.config.enable_human_behavior:
                await agent.scroll_down(random.randint(200, 400))
                await asyncio.sleep(random.uniform(0.5, 1.5))

            await agent.click(".next a")
            await asyncio.sleep(random.uniform(1.0, 2.0))
            page_num += 1

        # 保存结果
        result_path = Path("./output")
        result_path.mkdir(exist_ok=True)
        with open(result_path / "quotes.json", "w", encoding="utf-8") as f:
            json.dump(all_quotes, f, ensure_ascii=False, indent=2)

        logger.info("✅ 采集完成！共 %d 条数据", len(all_quotes))
        return all_quotes


async def demo_ecommerce_monitoring():
    """演示：电商价格监控（带会话持久化）。"""
    config = StealthAgentConfig(
        headless=True,
        enable_human_behavior=True,
        session_storage_dir="./sessions",
        screenshot_dir="./screenshots",
    )

    async with StealthAgent(config) as agent:
        await agent.navigate("https://books.toscrape.com")

        products = []
        page_num = 1

        while page_num <= 2:
            logger.info("📦 扫描第 %d 页商品...", page_num)

            titles = await agent.extract_all_texts("h3 a")
            prices = await agent.extract_all_texts(".price_color")
            availabilities = await agent.extract_all_texts(".availability")

            for i in range(len(titles)):
                products.append({
                    "title": titles[i] if i < len(titles) else "",
                    "price": prices[i] if i < len(prices) else "",
                    "available": "In stock" in (availabilities[i] if i < len(availabilities) else ""),
                })

            next_btn = await agent.extract_text(".next a")
            if not next_btn:
                break

            await agent.scroll_down()
            await agent.click(".next a")
            await asyncio.sleep(random.uniform(1.0, 2.0))
            page_num += 1

        logger.info("✅ 扫描完成！共 %d 件商品", len(products))

        # 保存为 CSV
        import csv
        output_path = Path("./output")
        output_path.mkdir(exist_ok=True)
        with open(output_path / "books.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "price", "available"])
            writer.writeheader()
            writer.writerows(products)

        return products


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(demo_collect_quotes())
```

---

## 9. 自动化检测的对抗手段总结

| 对抗手段 | 检测原理 | Stealth 应对方案 | 效果 |
|---------|---------|----------------|------|
| `navigator.webdriver` 检测 | Playwright/Selenium 会设置该标记为 `true` | `add_init_script` 覆盖为 `undefined` | ✅ 完全绕过 |
| Chrome 对象检测 | 无头模式缺少 `window.chrome` | 仿真构造完整 `chrome` 对象 | ✅ 完全绕过 |
| 插件列表检测 | 无头模式 `plugins.length == 0` | 注入包含 PDF/Chrome 扩展的伪插件列表 | ✅ 完全绕过 |
| WebGL 渲染器检测 | 无头模式渲染器含 `SwiftShader` | 替换为真实显卡信息(如 NVIDIA GeForce) | ✅ 完全绕过 |
| Canvas 指纹 | 自动化 Canvas 输出与真实浏览器不同 | 添加 ±1 像素噪声使指纹差异合理化 | ⚠️ 有效 |
| AudioContext 指纹 | 自动化环境无音频设备 | 对频率响应数据添加噪声 | ⚠️ 有效 |
| 字体枚举检测 | 无头/容器环境字体稀少 | 通过网络请求或 JS 注入模拟字体列表 | ⚠️ 部分有效 |
| 行为分析 (鼠标轨迹) | 自动化的鼠标是直线跳跃 | 贝塞尔曲线 + 随机抖动 + 悬停延迟 | ✅ 非常有效 |
| 行为分析 (点击模式) | 自动化点击间隔均匀 | 随机化点击前/后延迟、坐标偏移 | ✅ 非常有效 |
| 行为分析 (输入速度) | 自动化文本瞬间填入 | 逐字符随机延迟输入、偶尔打错修正 | ✅ 非常有效 |
| 行为分析 (滚动) | 自动化从不滚动或匀速滚动 | 分阶段随机速度滚动、夹杂阅读停顿 | ✅ 非常有效 |
| IP 频率检测 | 短时间大量请求 | 代理轮换、请求间隔随机化 | ⚠️ 有效 |
| Cookie/Storage 一致性 | 自动化环境缺少浏览历史 | 会话持久化保持 Cookie、LocalStorage 连续性 | ✅ 有效 |
| 权限 API 检测 | 权限状态异常 | 设置合理的地理位置、通知权限 | ✅ 部分绕过 |
| TLS 指纹 (JA3) | 自动化库 TLS 握手特征不同 | 使用真实浏览器内核而非 HTTP 库 | ✅ 完全绕过 |
| CDP (Chrome DevTools Protocol) 检测 | 检测 DevTools 连接 | 无法完全隐藏，但可通过 `--remote-debugging-port` 混淆 | ⚠️ 有限 |

### 检测难易程度金字塔

```
                    🔴 极难绕过
                   /  行为分析
                  /  （鼠标轨迹、点击模式、输入节奏）
                 /
              🟠 较难绕过
             /   Canvas/WebGL/Audio 指纹
            /    字体枚举、权限 API
           /
        🟡 中等难度
       /   IP 频率检测、Cookie 一致性
      /    TLS 指纹 (JA3/JA3S)
     /
  🟢 较易绕过
  navigator.webdriver、window.chrome
  navigator.plugins、User-Agent
```

---

## 10. 附录

### 检测网站清单

| 站点 | URL | 说明 |
|------|-----|------|
| SannySoft Bot Detector | https://bot.sannysoft.com | 最直观的 Stealth 检测面板 |
| CreepJS | https://abrahamjuliot.github.io/creepjs/ | 深度浏览器指纹检测 |
| FingerprintJS | https://fingerprintjs.github.io/fingerprintjs/ | 专业指纹库演示 |
| AmIUnique | https://amiunique.org/fp | 指纹唯一性分析 |
| BrowserLeaks | https://browserleaks.com/ | 全面的浏览器特征泄露检测 |
| Cover Your Tracks | https://coveryourtracks.eff.org/ | EFF 的隐私检测工具 |
| Pixelscan | https://pixelscan.net/ | 自动化机器人检测 |

### Playwright Stealth 插件

除了手动实现外，也可使用社区维护的 Stealth 插件：

```bash
pip install playwright-stealth
```

```python
from playwright_stealth import stealth_sync

# 同步版
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    stealth_sync(page)
    page.goto("https://bot.sannysoft.com")

# 异步版
from playwright_stealth import stealth_async

async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    await stealth_async(page)
    await page.goto("https://bot.sannysoft.com")
```

---

> **核心原则**：没有万能的 Stealth 方案，网站的反检测技术在持续演进。最佳策略是 **多层防御**（启动参数 → 上下文配置 → JS 特征覆盖 → 行为模拟），并根据目标网站的检测强度不断调整配置。对于高安全要求的场景，可以通过 `StealthChecker` 工具定期评估并优化配置。
