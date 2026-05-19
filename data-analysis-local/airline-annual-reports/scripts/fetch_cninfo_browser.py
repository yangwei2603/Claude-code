#!/usr/bin/env python3
"""
使用 playwright 浏览器自动化从巨潮资讯下载年报 PDF
步骤：
1. 浏览器访问 cninfo 股票页面
2. 定位到年报公告列表
3. 找到正确年报的下载按钮
4. 下载 PDF 到本地

用法:
    python3 fetch_cninfo_browser.py 2024
    python3 fetch_cninfo_browser.py 2023 2024 2025
"""
import os
import sys
import json
import time
from pathlib import Path

# 添加项目根目录到 path
PROJECT_ROOT = Path(__file__).parent.parent
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

# 目标航司
AIRLINES = {
    "春秋航空": {"code": "601021", "org_id": "gssz0601021"},
    "吉祥航空": {"code": "603885", "org_id": "gssz0603885"},
    "中国国航": {"code": "601111", "org_id": "gssz0601111"},
    "中国东航": {"code": "600115", "org_id": "gssz0600115"},
    "中国南航": {"code": "600029", "org_id": "gssz0600029"},
    "海航控股": {"code": "600221", "org_id": "gssz0600221"},
    "华夏航空": {"code": "002928", "org_id": "gssz0002928"},
}


def process_one(browser, airline: str, info: dict, year: int) -> dict:
    """用浏览器处理单个航司单年"""
    from playwright.sync_api import sync_playwright

    stock_code = info["code"]
    org_id = info["org_id"]
    save_path = DOWNLOADS_DIR / f"{airline}_{year}_年报.pdf"

    if save_path.exists():
        size_kb = save_path.stat().st_size // 1024
        print(f"  [已有] {save_path.name} ({size_kb}KB)")
        return {"airline": airline, "year": year, "status": "exists", "path": str(save_path)}

    context = browser.contexts[0] if browser.contexts else browser.new_context(
        accept_downloads=True,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = context.pages[0] if context.pages else context.new_page()

    try:
        # 访问公司披露列表页
        url = f"https://www.cninfo.com.cn/new/disclosure/list?plate=sse&stockCode={stock_code}&orgId={org_id}"
        print(f"  访问: {url}")
        page.goto(url, timeout=30000)
        page.wait_for_load_state("networkidle", timeout=20000)
        page.wait_for_timeout(2000)

        # 等待公告列表加载
        # 巨潮资讯的列表容器可能是 .list > .item 或类似的
        selectors_to_try = [
            ".announcement-list",
            ".list .announce-item",
            ".company-report",
            "table.announcement-table",
            ".report-list",
        ]

        list_loaded = False
        for sel in selectors_to_try:
            try:
                page.wait_for_selector(sel, timeout=5000)
                list_loaded = True
                print(f"  找到列表容器: {sel}")
                break
            except:
                continue

        if not list_loaded:
            # 打印页面结构用于调试
            html = page.content()
            # 保存调试文件
            debug_file = DOWNLOADS_DIR / f"debug_{airline}_{year}.html"
            with open(debug_file, "w") as f:
                f.write(html)
            print(f"  [警告] 未找到公告列表，已保存调试文件: {debug_file.name}")
            return {"airline": airline, "year": year, "status": "list_not_found", "debug": str(debug_file)}

        # 提取所有年报条目
        # 查找包含"年报"且包含年份的链接（排除"摘要"）
        rows = page.query_selector_all("tr, .item, .announce-item, .report-item")

        target_link = None
        target_text = ""

        # 方式1: 找表格行
        for row in page.query_selector_all("tr"):
            text = row.inner_text() or ""
            if "年报" in text and str(year) in text and "摘要" not in text and "补充" not in text:
                # 找这一行的下载链接
                link = row.query_selector("a[href*='download'], a.download-btn, .download-btn")
                if not link:
                    link = row.query_selector("a")
                if link:
                    href = link.get_attribute("href") or ""
                    target_link = href if href.startswith("http") else "https://www.cninfo.com.cn" + href
                    target_text = text.strip().replace("\n", " ")[:80]
                    break

        # 方式2: 找普通元素
        if not target_link:
            all_links = page.query_selector_all("a")
            for link in all_links:
                text = link.inner_text() or ""
                href = link.get_attribute("href") or ""
                if "年报" in text and str(year) in text and "摘要" not in text and "补充" not in text:
                    target_link = href if href.startswith("http") else "https://www.cninfo.com.cn" + href
                    target_text = text.strip()
                    break

        if not target_link:
            print(f"  [未找到] {year} 年度报告条目")
            return {"airline": airline, "year": year, "status": "not_found"}

        print(f"  找到: {target_text}")
        print(f"  链接: {target_link[:80]}")

        # 点击下载
        # 找到对应链接并点击触发下载
        for row in page.query_selector_all("tr"):
            text = row.inner_text() or ""
            if "年报" in text and str(year) in text and "摘要" not in text:
                # 找这一行的下载按钮
                download_link = None
                for a in row.query_selector_all("a"):
                    href = a.get_attribute("href") or ""
                    title = a.get_attribute("title") or ""
                    if "下载" in title or "pdf" in href.lower() or "download" in href.lower():
                        download_link = a
                        break
                if not download_link:
                    # 找最后一个 a 标签（通常是操作列的查看/下载）
                    links_in_row = row.query_selector_all("a")
                    if links_in_row:
                        download_link = links_in_row[-1]

                if download_link:
                    with page.expect_download(timeout=30000) as download_info:
                        download_link.click()
                    dl = download_info.value
                    dl.save_as(save_path)
                    size_kb = save_path.stat().st_size // 1024
                    print(f"  [成功] {save_path.name} ({size_kb}KB)")
                    return {"airline": airline, "year": year, "status": "downloaded", "path": str(save_path), "size_kb": size_kb}

        # 直接用链接下载
        if target_link:
            page.download(url=target_link, path=save_path)
            if save_path.exists():
                size_kb = save_path.stat().st_size // 1024
                print(f"  [成功] {save_path.name} ({size_kb}KB)")
                return {"airline": airline, "year": year, "status": "downloaded", "path": str(save_path), "size_kb": size_kb}

        print(f"  [失败] 未能下载")
        return {"airline": airline, "year": year, "status": "download_failed"}

    except Exception as e:
        print(f"  [异常] {e}")
        return {"airline": airline, "year": year, "status": "error", "error": str(e)}


def main():
    years = [int(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else [2024]

    print(f"{'='*60}")
    print("航空年报 PDF 下载工具（playwright 浏览器版）")
    print(f"目标年份: {years}")
    print(f"保存目录: {DOWNLOADS_DIR}")
    print(f"{'='*60}")

    from playwright.sync_api import sync_playwright

    all_results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=True
        )
        context = browser.new_context(
            accept_downloads=True,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        for year in years:
            print(f"\n{'='*50}")
            print(f"下载 {year} 年度报告")
            print(f"{'='*50}")

            year_results = {}
            for airline, info in AIRLINES.items():
                print(f"\n[{airline}]({info['code']})")
                result = process_one(browser, airline, info, year)
                year_results[airline] = result
                time.sleep(1)

            all_results[str(year)] = year_results

            # 保存中间结果
            results_file = DOWNLOADS_DIR / f"fetch_results_{year}.json"
            with open(results_file, "w", encoding="utf-8") as f:
                json.dump(year_results, f, ensure_ascii=False, indent=2)

            # 统计
            downloaded = sum(1 for v in year_results.values() if v["status"] == "downloaded")
            exists = sum(1 for v in year_results.values() if v["status"] == "exists")
            print(f"\n{year}年下载完成: 成功{downloaded}个, 已有{exists}个")

        browser.close()

    # 最终汇总
    print(f"\n{'='*60}")
    print("最终汇总:")
    for year_str, yr_data in all_results.items():
        for airline, r in yr_data.items():
            status_icon = {"downloaded": "✓", "exists": "●", "not_found": "✗", "error": "!"}.get(r["status"], "?")
            size = f"({r.get('size_kb', 0)}KB)" if "size_kb" in r else ""
            print(f"  {status_icon} {airline} {year_str}: {r['status']} {size}")

    pdfs = list(DOWNLOADS_DIR.glob("*.pdf"))
    print(f"\n共 {len(pdfs)} 个 PDF 文件")
    for pdf in sorted(pdfs)[:20]:
        print(f"  {pdf.name} ({pdf.stat().st_size // 1024}KB)")


if __name__ == "__main__":
    main()
