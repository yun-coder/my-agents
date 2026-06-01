"""Playwright 浏览器自动化的显式执行示例。"""

from __future__ import annotations

import argparse
import asyncio


TARGET_URL = "https://example.com"


async def inspect_page() -> None:
    """打开公开测试页并读取标题，不执行写操作。"""

    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(TARGET_URL)
        print({"url": page.url, "title": await page.title()})
        await browser.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="真正启动浏览器访问公开测试页")
    args = parser.parse_args()
    if not args.run:
        print({"mode": "dry-run", "target_url": TARGET_URL, "action": "read-title"})
        return
    asyncio.run(inspect_page())


if __name__ == "__main__":
    main()
