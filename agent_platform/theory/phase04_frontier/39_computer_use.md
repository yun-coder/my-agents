# 39 — Computer Use / GUI Agent

## 概念概述

### 什么是 Computer Use

Computer Use（计算机使用）是指 AI Agent 直接操作计算机图形用户界面（GUI）的能力——看屏幕截图、移动鼠标、点击按钮、键入文本——就像人类操作电脑一样。传统的 API 集成通过 JSON/HTTP 与软件交互，而 Computer Use Agent 则通过视觉像素输入和模拟物理输入输出来完成操作。

2024 年 10 月，Anthropic 在 Claude 3.5 Sonnet 中首次推出了 Computer Use API（公测版），这是主流大模型厂商首次将"看屏幕并操作电脑"作为原生能力公开提供。这一能力突破了传统 API 的边界，使得 Agent 可以操作那些没有 API、只有图形界面的遗留系统。

### GUI Agent 的技术栈

完整的 Computer Use Agent 由以下层次构成：

- 感知层（Perception Layer）：截图捕获，屏幕区域识别，像素级分析
- 推理层（Reasoning Layer）：目标拆解，动作规划，风险评估
- 执行层（Action Layer）：鼠标控制，键盘输入，拖拽操作
- 反馈层（Feedback Loop）：结果截图对比，执行验证，错误重试

### 适用场景

GUI Agent 特别适合以下场景：

- 遗留系统自动化：没有 API 的 20 年老系统（银行终端、ERP、医院 HIS）
- 跨平台操作：需要同时操作 Windows、Mac、Linux 桌面应用
- QA 测试自动化：Web/桌面应用的视觉回归测试
- 数据录入流水线：从 PDF/图片中读取数据并录入表单
- RPA 替代方案：传统 RPA 需要录制脚本，GUI Agent 通过自然语言描述即可操作

---

## 核心原理

### 截图到动作的闭环循环

Computer Use Agent 的核心运行机制是一个闭环循环：

```
步骤 1 — CAPTURE：  获取当前屏幕截图（全屏或特定区域）
步骤 2 — PERCEIVE： 将截图送入多模态模型（如 Claude 3.5 Sonnet）
步骤 3 — REASON：   模型分析截图内容，决定下一步动作
步骤 4 — ACT：      执行动作（移动鼠标、点击、键入等）
步骤 5 — OBSERVE：  捕获执行后的新截图
步骤 6 — REPEAT：   回到步骤 2，直到任务完成
```

每一步的截图都会作为下一轮的输入，形成连续的视觉上下文。这种"看见-思考-行动-再看"的循环是 GUI Agent 区别于传统脚本自动化的核心特征。

### Anthropic Computer Use API

Anthropic 的 Computer Use API 通过 `computer_use_20241022` 工具定义实现。核心思路是让模型返回结构化的"工具调用"，其中包含要在计算机上执行的操作。

```python
import anthropic

client = anthropic.Anthropic(api_key="YOUR_API_KEY")

def computer_use_loop(prompt: str, max_turns: int = 20):
    """
    Anthropic Computer Use API 的主循环

    Args:
        prompt: 描述要完成的任务
        max_turns: 最大交互轮次（防止无限循环）
    """
    messages = [{"role": "user", "content": prompt}]

    for turn in range(max_turns):
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            messages=messages,
            tools=[{
                "type": "computer_use_20241022",
                "name": "computer",
                "display_width_px": 1920,
                "display_height_px": 1080,
                "display_number": 1
            }]
        )

        for content in response.content:
            if content.type == "text":
                print(f"[思考] {content.text}")

            elif content.type == "tool_use":
                tool_name = content.name
                tool_input = content.input

                if tool_name == "computer":
                    action = tool_input.get("action")
                    if action == "screenshot":
                        screenshot = capture_screenshot()
                        messages.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": content.id,
                                "content": [{
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/png",
                                        "data": screenshot
                                    }
                                }]
                            }]
                        })
                    elif action == "mouse_move":
                        x, y = tool_input["coordinate"]
                        move_mouse(x, y)
                    elif action == "click":
                        click_mouse(button=tool_input.get("button", "left"))
                    elif action == "type":
                        type_text(tool_input["text"])
                    elif action == "key":
                        press_key(tool_input["text"])
                    elif action == "double_click":
                        double_click()

                    new_screenshot = capture_screenshot()
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": [{
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": new_screenshot
                                }
                            }]
                        }]
                    })

        if any(
            hasattr(c, "text") and "[任务完成]" in c.text
            for c in response.content
        ):
            break

    return response
```

### 支持的动作类型

Computer Use API 支持以下动作类型：

| 动作        | 参数                                | 说明                     |
|-------------|-------------------------------------|--------------------------|
| screenshot  | 无                                  | 捕获当前屏幕截图         |
| mouse_move  | coordinate: [x, y]                  | 移动鼠标到指定坐标       |
| click       | button: left/right/middle           | 点击鼠标按钮             |
| double_click| 无                                  | 双击鼠标                 |
| type        | text: str                           | 键入文本                 |
| key         | text: str                           | 按下特殊按键             |
| drag        | start: [x,y], end: [x,y]            | 从起点拖拽到终点         |
| scroll      | x, y, scroll_x, scroll_y            | 滚动页面                 |

### 安全边界设计

Anthropic 为 Computer Use API 设计了多层安全防护机制：

```python
class ComputerUseSafety:
    """Computer Use 安全边界实现"""

    # 危险操作黑名单
    BLOCKED_ACTIONS = {
        "shutdown": r"(shutdown|关机|shutdown命令)",
        "format": r"(format|格式化|mkfs)",
        "rm_rf": r"(rm -rf|删除所有文件)",
        "sudo_rm": r"(sudo rm|管理员删除)",
    }

    # 敏感区域（不允许点击的区域）
    SENSITIVE_ZONES = [
        {"name": "taskbar", "x_range": (0, 1920), "y_range": (1040, 1080)},
        {"name": "start_menu", "x_range": (0, 60), "y_range": (1040, 1080)},
    ]

    @classmethod
    def validate_action(cls, action: str, params: dict) -> bool:
        """验证操作是否安全"""
        if action == "key":
            text = params.get("text", "")
            for blocked_name, pattern in cls.BLOCKED_ACTIONS.items():
                import re
                if re.search(pattern, text, re.IGNORECASE):
                    print(f"阻止危险操作: {blocked_name}")
                    return False

        if action in ("mouse_move", "click", "double_click"):
            if "coordinate" in params:
                x, y = params["coordinate"]
                for zone in cls.SENSITIVE_ZONES:
                    if (zone["x_range"][0] <= x <= zone["x_range"][1]
                            and zone["y_range"][0] <= y <= zone["y_range"][1]):
                        print(f"阻止在敏感区域操作: {zone['name']}")
                        return False

        return True
```

---

## 实战指南

### 环境准备

```bash
pip install anthropic pyautogui pillow opencv-python numpy
pip install mss          # 高性能截图库
pip install pynput       # 键盘/鼠标监听
```

macOS 需要额外授权：系统设置 — 隐私与安全性 — 辅助功能 — 允许终端，以及屏幕录制权限。Windows 上 pyautogui 直接可用。Linux 需安装依赖：`sudo apt-get install python3-xlib scrot`。

### 截图工具封装

```python
import mss
import base64
from io import BytesIO
from PIL import Image

class ScreenCapture:
    """跨平台高性能截图工具，使用 mss 库"""

    def __init__(self, monitor: int = 1):
        self.sct = mss.mss()
        self.monitor = monitor

    def capture(self) -> bytes:
        """截图并返回 PNG 字节数据"""
        monitor_data = self.sct.monitors[self.monitor]
        sct_img = self.sct.grab(monitor_data)
        img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def capture_to_base64(self) -> str:
        """截图并返回 base64 编码字符串"""
        png_data = self.capture()
        return base64.b64encode(png_data).decode("utf-8")

    def capture_region(self, x: int, y: int, w: int, h: int) -> bytes:
        """截取指定区域"""
        region = {"top": y, "left": x, "width": w, "height": h}
        sct_img = self.sct.grab(region)
        img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
```

### 鼠标键盘控制器

```python
import pyautogui

class GUIAutomation:
    """图形界面自动化控制器"""

    def __init__(self):
        pyautogui.FAILSAFE = True  # 鼠标移到左上角紧急停止
        pyautogui.PAUSE = 0.1
        self.screen_width, self.screen_height = pyautogui.size()

    def click(self, x: int, y: int, button: str = "left"):
        pyautogui.click(x, y, button=button)

    def double_click(self, x: int, y: int):
        pyautogui.doubleClick(x, y)

    def right_click(self, x: int, y: int):
        pyautogui.rightClick(x, y)

    def type_text(self, text: str):
        pyautogui.write(text, interval=0.02)

    def press_key(self, key: str):
        pyautogui.press(key)

    def hotkey(self, *keys: str):
        pyautogui.hotkey(*keys)

    def scroll(self, clicks: int, x: int = None, y: int = None):
        pyautogui.scroll(clicks, x, y)

    def find_and_click(self, image_path: str, confidence: float = 0.8):
        """通过图像识别查找并点击"""
        location = pyautogui.locateOnScreen(image_path, confidence=confidence)
        if location:
            center = pyautogui.center(location)
            pyautogui.click(center)
            return center
        return None
```

### 完整 Computer Use Agent

```python
from dataclasses import dataclass
import anthropic

@dataclass
class ComputerAgentConfig:
    api_key: str
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4096
    max_turns: int = 50
    display_width: int = 1920
    display_height: int = 1080
    display_number: int = 1
    safety_enabled: bool = True

class ComputerAgent:
    """通用 Computer Use Agent"""

    def __init__(self, config: ComputerAgentConfig):
        self.config = config
        self.client = anthropic.Anthropic(api_key=config.api_key)
        self.screen = ScreenCapture()
        self.gui = GUIAutomation()

    def run(self, task: str) -> dict:
        messages = self._build_initial_messages(task)

        for turn in range(self.config.max_turns):
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                messages=messages,
                tools=[self._computer_tool()]
            )

            for content in response.content:
                if content.type == "text":
                    messages.append({"role": "assistant", "content": content.text})
                elif content.type == "tool_use":
                    self._execute_tool(content, messages)

            if any(
                hasattr(c, "text") and "任务完成" in c.text
                for c in response.content
            ):
                return {"status": "completed", "turns": turn + 1}

        return {"status": "max_turns_exceeded"}

    def _computer_tool(self) -> dict:
        return {
            "type": "computer_use_20241022",
            "name": "computer",
            "display_width_px": self.config.display_width,
            "display_height_px": self.config.display_height,
            "display_number": self.config.display_number,
        }

    def _build_initial_messages(self, task: str) -> list:
        screenshot = self.screen.capture_to_base64()
        return [{
            "role": "user",
            "content": [
                {"type": "text", "text": f"请帮我完成以下任务: {task}"},
                {"type": "image", "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": screenshot
                }}
            ]
        }]

    def _execute_tool(self, tool_use, messages):
        action = tool_use.input.get("action")
        params = tool_use.input

        if self.config.safety_enabled:
            if not ComputerUseSafety.validate_action(action, params):
                messages.append({"role": "user", "content": f"操作被安全策略阻止: {action}"})
                return

        messages.append({
            "role": "assistant",
            "content": [{"type": "tool_use", "id": tool_use.id,
                         "name": tool_use.name, "input": tool_use.input}]
        })

        if action == "screenshot":
            screenshot = self.screen.capture_to_base64()
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": [{"type": "image", "source": {
                        "type": "base64", "media_type": "image/png",
                        "data": screenshot
                    }}]
                }]
            })
        else:
            self._perform_action(action, params)
            new_shot = self.screen.capture_to_base64()
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": [
                        {"type": "text", "text": f"已执行 {action}"},
                        {"type": "image", "source": {
                            "type": "base64", "media_type": "image/png",
                            "data": new_shot
                        }}
                    ]
                }]
            })

    def _perform_action(self, action: str, params: dict):
        if action == "mouse_move":
            self.gui.click(params["coordinate"][0], params["coordinate"][1])
        elif action == "click":
            x, y = params.get("coordinate", (None, None))
            if x and y:
                self.gui.click(x, y, params.get("button", "left"))
        elif action == "double_click":
            x, y = params.get("coordinate")
            self.gui.double_click(x, y)
        elif action == "type":
            self.gui.type_text(params["text"])
        elif action == "key":
            self.gui.press_key(params["text"])
```

---

## Browser Use 框架

Browser Use 是一个开源框架，专门让 AI Agent 控制浏览器。它通过 DOM 解析和 CSS 选择器实现精确定位，比通用 Computer Use 更高效。

```python
from browser_use import Agent, Browser

browser = Browser(headless=False)
agent = Agent(
    browser=browser,
    task="登录 Gmail 并查找上周的邮件",
    model="claude-sonnet-4-20250506",
    max_steps=30
)
result = await agent.run()
```

### Browser Use vs Computer Use 对比

| 特性       | Browser Use        | Computer Use      |
|------------|--------------------|-------------------|
| 操作范围   | 仅浏览器           | 整个桌面          |
| DOM 能力   | 直接访问 DOM       | 仅视觉像素        |
| 定位精度   | CSS/XPath 选择器   | 像素坐标          |
| 速度       | 快（结构化交互）    | 慢（截图分析）     |
| 遗留系统   | 不支持             | 支持              |

### 混合架构

将两者结合：Web 场景走 Browser Use，系统操作走 Computer Use。

```python
class HybridAgent:
    def __init__(self, computer_agent: ComputerAgent):
        self.computer = computer_agent

    async def run(self, task: str):
        if any(kw in task for kw in ["浏览器", "网页", "登录", "搜索"]):
            return await self._run_browser(task)
        return self.computer.run(task)
```

---

## RPA 对比分析

### 传统 RPA 的局限

传统的 RPA（如 UiPath、Blue Prism、影刀）依赖预先录制的脚本和固定选择器。界面一旦变化就需要重新录制，维护成本极高。

### AI GUI Agent 的优势

GUI Agent 通过视觉理解适应界面变化。不需要预录脚本，直接用自然语言描述任务即可：

- 传统 RPA："在坐标 (100,200) 处点击按钮，等待 2 秒，在坐标 (300,400) 处输入文本"
- GUI Agent："打开 SAP 客户端，输入用户名 admin，密码 pass123，点击登录"

### 对比总结

| 维度     | 传统 RPA        | AI GUI Agent   |
|----------|-----------------|----------------|
| 脚本方式 | 录制/拖拽        | 自然语言描述    |
| 适应性   | 脆弱（选择器依赖）| 强（视觉理解）  |
| 异常处理 | 需预编逻辑       | 模型自主推理    |
| 速度     | 快（毫秒级）     | 慢（含 LLM 推理）|
| 成本     | 许可费高         | API 按量计费    |

---

## 最佳实践

### 提供清晰的初始截图

在任务开始时给 Agent 提供当前桌面截图，帮助模型了解起始状态。

### 合理的任务粒度

复杂任务应拆分为子任务，每一步给出明确的上下文：

```python
# 推荐：逐步执行
tasks = [
    "打开 Chrome 浏览器",
    "在地址栏输入 example.com",
    "点击页面上的登录按钮",
    "在用户名输入框中输入 admin"
]
```

### 坐标空间映射

不同分辨率下工作时需要坐标映射：

```python
class CoordinateMapper:
    def __init__(self, ref_width=1920, ref_height=1080):
        self.ref_w, self.ref_h = ref_width, ref_height
        self.actual_w, self.actual_h = pyautogui.size()

    def map(self, x: int, y: int) -> tuple:
        return (
            int(x * self.actual_w / self.ref_w),
            int(y * self.actual_h / self.ref_h),
        )
```

### 紧急停止机制

```python
import threading
import keyboard

class EmergencyStop:
    def __init__(self, hotkey: str = "ctrl+shift+x"):
        self.stopped = False
        threading.Thread(target=self._listen, daemon=True).start()

    def _listen(self):
        keyboard.wait(self.hotkey)
        self.stopped = True
        print("紧急停止!")
```

---

## 常见陷阱

### 陷阱 1：无限循环

Agent 在某个操作上不断重试。设置最大轮次限制，实现"三次重试后放弃"策略。

### 陷阱 2：坐标漂移

窗口位置变化后坐标失效。每次操作前重新截图确认位置，而不是依赖上一次的坐标缓存。

### 陷阱 3：权限不足

截图和模拟输入需要操作系统权限。macOS 需要 Accessibility 权限，Linux 需要 X11 配置。

### 陷阱 4：安全风险

Agent 可能执行危险操作（删除文件、关机）。必须实现安全边界检查机制。

---

## API Key 依赖

| 服务                | 所需 API Key         | 获取方式              |
|---------------------|----------------------|-----------------------|
| Anthropic Computer  | ANTHROPIC_API_KEY    | console.anthropic.com |
| Browser Use         | 无需/模型自有 key    | GitHub 开源           |

```bash
# .env 文件
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
```

本模块需要有效的 Anthropic API Key 才能使用 Computer Use 功能。API Key 应通过环境变量设置，避免硬编码在代码中。
ENDOFFILE