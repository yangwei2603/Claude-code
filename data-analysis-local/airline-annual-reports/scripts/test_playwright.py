#!/usr/bin/env python3
"""
测试 playwright + Chrome 是否可用
"""
from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        # 尝试使用已安装的 Chrome
        browser = p.chromium.launch(
            channel="chrome",
            headless=True
        )
        page = browser.new_page()
        page.goto("https://www.baidu.com")
        print("Chrome accessible:", page.title())
        browser.close()

if __name__ == "__main__":
    test()
