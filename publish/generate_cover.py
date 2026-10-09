#!/usr/bin/env python3
"""用 Playwright 对 HTML 文件截图生成封面"""
import asyncio, os, sys, json
from playwright.async_api import async_playwright

script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)

with open(os.path.join(script_dir, "publish-config.json"), encoding="utf-8") as f:
    cfg = json.load(f)

HTML_FILE = os.path.join(project_dir, cfg["htmlFile"])
OUTPUT = os.path.join(script_dir, "cover.png")

async def main():
    async with async_playwright() as p:
        browser = None
        for channel in ("msedge", "chrome", None):
            try:
                browser = await p.chromium.launch(channel=channel)
                break
            except Exception:
                continue
        if browser is None:
            print("ERROR: 未找到可用浏览器 (Edge/Chrome/Chromium)", file=sys.stderr)
            sys.exit(1)
        page = await browser.new_page(viewport={"width": 520, "height": 720}, device_scale_factor=2)
        await page.goto(f"file:///{HTML_FILE.replace(os.sep, '/')}")
        await page.wait_for_timeout(1500)
        card = await page.query_selector(".calendar")
        if card:
            await card.screenshot(path=OUTPUT)
        else:
            await page.screenshot(path=OUTPUT)
        await browser.close()
        print(f"封面已生成: {OUTPUT}")

asyncio.run(main())