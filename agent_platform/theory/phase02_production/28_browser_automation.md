# 28 浏览器自动化

## 概念概述

浏览器自动化是指通过程序控制浏览器执行各种操作的技术，包括页面导航、数据提取、表单填写、截图捕获等。在 AI Agent 领域，浏览器自动化被广泛应用于 Web 数据采集、自动化测试、RPA（机器人流程自动化）以及通过浏览器与不支持 API 的 Web 应用交互。

主流的浏览器自动化框架有三个：Playwright、Puppeteer 和 Selenium。Playwright 由微软开发，是当前最现代、功能最丰富的选择；Puppeteer 由 Google 开发，专注于 Chrome/Chromium；Selenium 是历史最悠久的框架，支持最广泛的浏览器种类。

Browser Use 是一个新兴的 AI 原生浏览器自动化框架，它将 LLM 与浏览器控制结合，让 AI Agent 能够像人类一样操作浏览器完成复杂任务。

### 三大框架对比

| 特性 | Playwright | Puppeteer | Selenium |
|------|-----------|-----------|----------|
| 浏览器支持 | Chromium, Firefox, WebKit | Chromium | 所有主流浏览器 |
| 语言支持 | JS, Python, Java, .NET | JS, TypeScript | 多语言 |
| 速度 | 快 | 快 | 中等 |
| 自动等待 | 内置 | 需手动 | 需手动 |
| 网络拦截 | 原生支持 | 原生支持 | 需中间代理 |
| 移动端模拟 | 支持 | 部分支持 | 支持 |
| 并行执行 | Browser Context | 多页面 | 多实例 |
| 维护状态 | 微软积极维护 | Google 维护中 | 社区维护 |

## 核心原理

### Playwright 核心概念

**Browser（浏览器实例）**：一个浏览器进程，可以启动 Chromium、Firefox 或 WebKit。

**Browser Context（浏览器上下文）**：隔离的浏览器会话，类似匿名模式。每个 Context 有独立的 Cookie、存储和缓存。这是 Playwright 最强大的特性之一，可以在同一个 Browser 中创建多个隔离的 Context。

**Page（页面）**：浏览器中的一个标签页，用于执行页面导航和交互操作。

**Locator（定位器）**：Playwright 的元素定位策略，支持 CSS 选择器、XPath、文本内容、角色等多种方式。定位器的自动等待机制是其核心优势。

**Auto-Waiting（自动等待）**：Playwright 在执行操作前会自动等待元素可交互，无需显式 sleep。

### 浏览器自动化典型流程

```
启动浏览器 -> 创建 Context -> 打开 Page -> 导航到 URL
                                           -> 等待元素加载
                                           -> 执行操作（点击/输入/提取）
                                           -> 验证结果
                                           -> 截图/数据保存
-> 关闭 Context -> 关闭 Browser
```

## 实战指南

### 使用 Playwright 进行页面导航与数据提取

```python
"""Playwright 基础用法：页面导航与数据提取。"""
import asyncio
import json
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright, Page, BrowserContext


async def basic_navigation() -> None:
    """基础页面导航示例。"""
    async with async_playwright() as p:
        # 启动浏览器（headless=False 可看到浏览器窗口）
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # 导航到目标页面
        await page.goto("https://example.com", wait_until="networkidle")

        # 获取页面标题
        title = await page.title()
        print(f"页面标题: {title}")

        # 获取页面内容
        content = await page.content()
        print(f"页面长度: {len(content)} 字符")

        # 截图
        await page.screenshot(path="./screenshots/example.png", full_page=True)

        await browser.close()


async def extract_data() -> list[dict[str, str]]:
    """从页面提取结构化数据。"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("https://quotes.toscrape.com", wait_until="networkidle")

        # 使用 CSS 选择器提取引文数据
        quotes_data: list[dict[str, str]] = []

        # 定位所有引文元素
        quote_elements = await page.query_selector_all(".quote")

        for element in quote_elements:
            text = await element.query_selector(".text")
            author = await element.query_selector(".author")
            tags = await element.query_selector_all(".tag")

            text_content = await text.inner_text() if text else ""
            author_content = await author.inner_text() if author else ""
            tags_content = [await tag.inner_text() for tag in tags]

            quotes_data.append({
                "text": text_content,
                "author": author_content,
                "tags": ", ".join(tags_content),
            })

        await browser.close()
        return quotes_data


async def form_automation() -> None:
    """表单自动填写示例。"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto("https://example.com/login", wait_until="networkidle")

        # 使用定位器填写表单（自动等待元素可交互）
        await page.locator("#username").fill("test_user")
        await page.locator("#password").fill("test_password")
        await page.locator("button[type='submit']").click()

        # 等待导航完成
        await page.wait_for_url("**/dashboard", timeout=5000)

        # 验证登录成功
        welcome = await page.locator(".welcome-message").inner_text()
        assert "欢迎" in welcome, "登录失败"

        await browser.close()


async def screenshot_capture(output_dir: str = "./screenshots") -> None:
    """截取页面截图的多种方式。"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={"width": 1280, "height": 720}
        )

        await page.goto("https://example.com")

        # 整页截图
        await page.screenshot(
            path=str(output_path / "full_page.png"),
            full_page=True,
        )

        # 区域截图（只截取某个元素）
        element = await page.query_selector("h1")
        if element:
            await element.screenshot(
                path=str(output_path / "element.png")
            )

        # 指定格式和质量
        await page.screenshot(
            path=str(output_path / "optimized.jpg"),
            type="jpeg",
            quality=80,
        )

        await browser.close()


if __name__ == "__main__":
    asyncio.run(extract_data())
```

### 使用 Playwright 的同步 API

```python
"""Playwright 同步 API 用法（更简单的写法）。"""
from playwright.sync_api import sync_playwright


def scrape_with_sync_api() -> None:
    """使用同步 API 进行网页抓取。"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://quotes.toscrape.com")

        # 提取数据
        quotes = page.locator(".quote").all()
        for quote in quotes[:5]:
            text = quote.locator(".text").inner_text()
            author = quote.locator(".author").inner_text()
            print(f"{author}: {text[:50]}...")

        browser.close()


def handle_pagination(max_pages: int = 5) -> list[dict[str, str]]:
    """处理分页：遍历多页数据。"""
    all_data: list[dict[str, str]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://quotes.toscrape.com")

        for page_num in range(max_pages):
            # 提取当前页数据
            quotes = page.locator(".quote").all()
            for quote in quotes:
                all_data.append({
                    "text": quote.locator(".text").inner_text(),
                    "author": quote.locator(".author").inner_text(),
                })

            # 点击"下一页"按钮
            next_button = page.locator(".next a")
            if next_button.count() == 0:
                break
            next_button.click()
            page.wait_for_load_state("networkidle")

        browser.close()

    return all_data
```

### 反检测与 Stealth 技术

```python
"""反检测技术：避免被识别为自动化工具。"""
import asyncio

from playwright.async_api import async_playwright


async def stealth_browser() -> None:
    """配置反检测浏览器。"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )

        # 修改 navigator.webdriver 属性
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            # 模拟真实浏览器特征
            permissions=["geolocation"],
            geolocation={"latitude": 39.9042, "longitude": 116.4074},
        )

        # 注入 JavaScript 覆盖自动化检测
        await context.add_init_script("""
            // 覆盖 webdriver 属性
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });

            // 覆盖 chrome 对象
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {},
            };

            // 覆盖 plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });

            // 覆盖 languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en'],
            });
        """)

        page = await context.new_page()

        # 访问检测页面验证
        await page.goto("https://bot.sannysoft.com", wait_until="networkidle")
        await page.screenshot(path="./screenshots/stealth_test.png")

        await browser.close()


async def respect_rate_limits() -> None:
    """尊重网站的速率限制。"""
    import random
    import time

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        urls = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3",
        ]

        for url in urls:
            await page.goto(url, wait_until="networkidle")
            print(f"已访问: {url}")

            # 随机延迟，模拟人类行为
            delay = random.uniform(2.0, 5.0)
            await asyncio.sleep(delay)

            # 模拟滚动行为
            await page.evaluate(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            await asyncio.sleep(random.uniform(0.5, 1.5))

        await browser.close()
```

### Browser Use 框架集成

```python
"""使用 Browser Use 框架让 AI Agent 操作浏览器。"""
import asyncio
import os
from typing import Any

from browser_use import Agent, Browser, BrowserConfig
from langchain_openai import ChatOpenAI


async def browser_use_example(task: str) -> str:
    """使用 Browser Use 让 AI 控制浏览器完成任务。"""
    # 配置浏览器
    browser = Browser(
        config=BrowserConfig(
            headless=False,  # 设为 True 可无头运行
            disable_security=True,
        )
    )

    # 配置 LLM（需要 OPENAI_API_KEY）
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.0,
    )

    # 创建 Agent
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        max_actions_per_step=5,
    )

    # 执行任务
    history = await agent.run(max_steps=20)
    result = history.final_result() or ""

    await browser.close()
    return result


async def browser_use_data_collection() -> list[dict[str, Any]]:
    """使用 Browser Use 收集结构化数据。"""
    browser = Browser(
        config=BrowserConfig(headless=True)
    )

    llm = ChatOpenAI(model="gpt-4o", temperature=0.0)

    agent = Agent(
        task=(
            "访问 Hacker News 首页，提取前 10 篇文章的标题和链接。"
            "将结果保存为 JSON 格式。"
        ),
        llm=llm,
        browser=browser,
    )

    history = await agent.run()
    result = history.final_result()

    await browser.close()

    import json
    data = json.loads(result) if result else []
    return data


if __name__ == "__main__":
    asyncio.run(
        browser_use_example(
            "在 GitHub 上搜索 'playwright-python'，"
            "打开第一个结果，获取 star 数量。"
        )
    )
```

### Cookie 管理与会话持久化

```python
"""Cookie 管理和会话持久化，避免重复登录。"""
import json
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright


class SessionManager:
    """浏览器会话管理器，支持 Cookie 持久化。"""

    def __init__(self, storage_path: str = "./browser_storage") -> None:
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def get_storage_file(self, session_name: str) -> Path:
        """获取存储文件路径。"""
        return self.storage_path / f"{session_name}.json"

    def save_session(self, session_name: str, context: Any) -> None:
        """保存当前会话的 Cookie 和存储。"""
        storage_file = self.get_storage_file(session_name)
        storage_state = context.storage_state()
        with storage_file.open("w", encoding="utf-8") as f:
            json.dump(storage_state, f, ensure_ascii=False, indent=2)
        print(f"会话已保存: {storage_file}")

    def load_session(self, session_name: str) -> dict[str, Any] | None:
        """加载之前保存的会话状态。"""
        storage_file = self.get_storage_file(session_name)
        if storage_file.exists():
            with storage_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def session_exists(self, session_name: str) -> bool:
        """检查会话是否存在。"""
        return self.get_storage_file(session_name).exists()


def login_with_session(session_name: str, login_url: str) -> None:
    """使用会话管理登录网站。"""
    manager = SessionManager()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        # 如果已有会话，直接恢复
        if manager.session_exists(session_name):
            storage = manager.load_session(session_name)
            context = browser.new_context(storage_state=storage)
            page = context.new_page()
            page.goto(login_url)
            print("已恢复之前的登录会话")
        else:
            # 首次登录
            context = browser.new_context()
            page = context.new_page()
            page.goto(login_url)

            # 在这里手动登录，或者执行自动登录
            input("请手动登录，完成后按 Enter 继续...")

            # 保存会话
            manager.save_session(session_name, context)
            print("登录会话已保存")

        # 后续操作
        page.goto("https://example.com/dashboard")
        page.screenshot(path="./screenshots/dashboard.png")

        browser.close()
```

## 最佳实践

1. **优先使用 Playwright**：作为最新的浏览器自动化框架，Playwright 在速度、稳定性和功能全面性上优于 Puppeteer 和 Selenium。

2. **总是使用 Headless 模式**：非必要不显示浏览器窗口，提高运行效率并减少资源消耗。

3. **善用自动等待机制**：不要使用 `time.sleep()`，使用 Playwright 内置的自动等待（Auto-Waiting）机制。

4. **处理动态内容**：对于 JavaScript 渲染的页面，使用 `wait_for_selector` 或 `wait_for_load_state` 确保目标元素已加载。

5. **错误重试与超时管理**：网络请求可能失败，为关键操作添加重试逻辑和合理的超时设置。

6. **尊重 robots.txt 和速率限制**：避免对服务器造成过大压力，实现请求间隔和并发控制。

## 常见陷阱

1. **被网站检测为机器人**：越来越多的网站使用反自动化技术。需要使用 Stealth 技术修改浏览器特征。

2. **XPath / CSS 选择器不稳定**：页面结构变化会导致定位失败。优先使用有语义的 data 属性或文本内容定位。

3. **忽略资源加载**：页面可能包含数百个资源请求，设置合适的 `wait_until` 条件避免过早执行操作。

4. **Cookie 管理不当**：未正确处理会话导致频繁登录。使用 session 持久化机制。

5. **并行执行冲突**：多个自动化任务共享同一个浏览器实例会导致状态干扰。使用独立的 Context 隔离。

## API Key 依赖

浏览器自动化的 API Key 需求：

- **Playwright / Puppeteer / Selenium**：不需要 API Key
- **Browser Use 框架**：需要 LLM API Key（如 `OPENAI_API_KEY`）用于 AI Agent 决策
- **网页内容提取**：不需要 API Key
- **云端浏览器服务**（如 BrowserStack、SauceLabs）：需要服务 API Key

## 技术关系

浏览器自动化在 AI Agent 生态中的应用：

- **[RAG 评估](../phase02_production/24_rag_evaluation.md)**：自动化浏览器测试可以用于评估 Web 交互的 Agent 行为
- **[代码执行沙箱](../phase02_production/29_code_sandbox.md)**：浏览器自动化脚本可以在沙箱中安全执行
- **[Docker 部署](../phase02_production/30_docker_compose.md)**：浏览器自动化通常在 Docker 容器中运行，需要配置无头模式
- **AI Agent 工具**：浏览器操作可作为 Agent 的一个工具使用

## 验收清单

- [ ] 可以使用 Playwright 打开网页并提取数据
- [ ] 实现了表单自动化填写和提交
- [ ] 支持页面截图和区域截图
- [ ] 实现了反检测 Stealth 配置
- [ ] 处理了分页数据采集
- [ ] 实现了会话持久化管理
- [ ] 集成了 Browser Use 框架
- [ ] 设置了请求间隔和速率控制
- [ ] 正确处理了动态内容和异步加载
- [ ] 实现了完善的错误重试机制

## 学习资源

- [Playwright Python 文档](https://playwright.dev/python/docs/intro)
- [Puppeteer 文档](https://pptr.dev/)
- [Browser Use 框架](https://github.com/browser-use/browser-use)
- [Selenium 文档](https://www.selenium.dev/documentation/)
- [Playwright Stealth](https://github.com/nicedayzhu/playwright-stealth)
