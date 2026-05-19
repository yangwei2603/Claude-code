#!/usr/bin/env python3
"""
从巨潮资讯下载年报 PDF（使用 curl 命令，非 requests 库）
兼容受限网络环境

用法:
    python3 fetch_cninfo.py 2024          # 下载2024年年报
    python3 fetch_cninfo.py 2023 2024     # 下载多 年年报
"""
import os
import sys
import json
import subprocess
import time
import tempfile
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

# 目标航司（股票代码）
AIRLINES = {
    "中国国航": "601111",
    "中国东航": "600115",
    "中国南航": "600029",
    "春秋航空": "601021",
    "吉祥航空": "603885",
    "海航控股": "600221",
    "华夏航空": "002928",
}


def curl_download(url: str, output_path: Path, cookies: str = None) -> bool:
    """用 curl 下载文件"""
    cmd = ["curl", "-s", "-L", "-o", str(output_path), "--max-time", "30"]
    if cookies:
        cmd += ["-H", f"Cookie: {cookies}"]
    cmd.append(url)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 10000:
        return True
    return False


def curl_post_json(url: str, data: dict, headers: dict = None) -> dict:
    """用 curl POST 获取 JSON"""
    header_args = []
    if headers:
        for k, v in headers.items():
            header_args += ["-H", f"{k}: {v}"]

    data_args = []
    for k, v in data.items():
        data_args += ["-d", f"{k}={v}"]

    cmd = ["curl", "-s", "-X", "POST", "-L", "--max-time", "30"] + header_args + data_args + [url]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0 and result.stdout:
        try:
            return json.loads(result.stdout)
        except:
            return {}
    return {}


def fetch_yearbook_list(stock_code: str, year: int) -> list:
    """查询某公司某年的年报列表"""
    url = "https://www.cninfo.com.cn/new/hisAnnouncement/query"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://www.cninfo.com.cn",
        "Referer": f"https://www.cninfo.com.cn/new/disclosure/list?plate=sse&stockCode={stock_code}&orgId=",
    }

    post_data = {
        "stockCode": stock_code,
        "plate": "sse",
        "announcementYear": year,
        "pageNum": 1,
        "pageSize": 10,
        "column": "szse",
        "category": "category_ndbg_szsh",
        "isHLender": "false",
    }

    data_args = []
    for k, v in post_data.items():
        data_args += ["-d", f"{k}={v}"]

    header_args = []
    for k, v in headers.items():
        header_args += ["-H", f"{k}: {v}"]

    cmd = ["curl", "-s", "-X", "POST", "--max-time", "30"] + header_args + data_args + [url]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0 or not result.stdout:
        return []

    try:
        j = json.loads(result.stdout)
        return j.get("announcements", [])
    except:
        return []


def get_pdf_url_from_announcement(ann: dict) -> str:
    """从公告信息中提取 PDF 下载地址"""
    # attachment 字段包含 PDF 信息
    attachment = ann.get("attachment", {})
    if isinstance(attachment, str):
        try:
            attachment = json.loads(attachment)
        except:
            return ""

    if isinstance(attachment, dict):
        download_path = attachment.get("downloadPath", "")
        if download_path:
            return "https://www.cninfo.com.cn" + download_path

    return ""


def download_pdf(url: str, output_path: Path) -> bool:
    """下载 PDF"""
    # 从 URL 提取 cookie 信息
    cmd = [
        "curl", "-s", "-L", "-o", str(output_path),
        "--max-time", "45",
        "-A", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "-H", "Accept: application/pdf,text/html,application/xhtml+xml,*/*",
        "-H", "Referer: https://www.cninfo.com.cn/",
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 10000


def process_one(airline: str, stock_code: str, year: int) -> dict:
    """处理单个航司单年数据"""
    save_path = DOWNLOADS_DIR / f"{airline}_{year}_年报.pdf"

    if save_path.exists():
        size_kb = save_path.stat().st_size // 1024
        print(f"  [已有] {save_path.name} ({size_kb}KB)")
        return {"airline": airline, "year": year, "status": "exists", "path": str(save_path), "size_kb": size_kb}

    print(f"  查询 {airline}({stock_code}) {year} 年报...", end=" ", flush=True)

    announcements = fetch_yearbook_list(stock_code, year)

    # 过滤出年报（非摘要）
    target = None
    for ann in announcements:
        title = ann.get("announcementTitle", "")
        if "年报" in title and str(year) in title and "摘要" not in title and "补充" not in title:
            target = ann
            break

    if not target:
        print(f"[未找到]")
        # 也尝试"年度报告"匹配
        for ann in announcements:
            title = ann.get("announcementTitle", "")
            if "年度报告" in title and str(year) in title:
                target = ann
                break

        if not target:
            return {"airline": airline, "year": year, "status": "not_found", "announcements_found": [a.get("announcementTitle","") for a in announcements[:5]]}

    title = target.get("announcementTitle", "")
    print(f"[找到] {title}")

    pdf_url = get_pdf_url_from_announcement(target)
    if not pdf_url:
        # 备选：从 attachment 字段直接取
        attachment = target.get("attachment", {})
        if isinstance(attachment, dict):
            pdf_url = "https://www.cninfo.com.cn" + attachment.get("downloadPath", "")

    if not pdf_url:
        print(f"  [错误] 无法获取 PDF 下载地址")
        return {"airline": airline, "year": year, "status": "no_pdf_url", "ann": target}

    print(f"  下载 PDF: {pdf_url[:70]}...")
    success = download_pdf(pdf_url, save_path)

    if success:
        size_kb = save_path.stat().st_size // 1024
        print(f"  [成功] {save_path.name} ({size_kb}KB)")
        return {"airline": airline, "year": year, "status": "downloaded", "path": str(save_path), "size_kb": size_kb, "pdf_url": pdf_url}
    else:
        print(f"  [失败] curl 返回非零或文件过小")
        return {"airline": airline, "year": year, "status": "download_failed", "pdf_url": pdf_url}


def main():
    years = [int(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else [2024]

    print(f"{'='*60}")
    print("航空年报 PDF 下载工具（curl 版）")
    print(f"目标年份: {years}")
    print(f"保存目录: {DOWNLOADS_DIR}")
    print(f"{'='*60}")

    all_results = {}

    for year in years:
        print(f"\n{'='*50}")
        print(f"开始下载 {year} 年度报告")
        print(f"{'='*50}")

        year_results = {}
        for airline, stock_code in AIRLINES.items():
            print(f"\n[{airline}]")
            result = process_one(airline, stock_code, year)
            year_results[airline] = result
            time.sleep(0.5)  # 礼貌性限速

        all_results[str(year)] = year_results

        # 中间保存
        results_file = DOWNLOADS_DIR / f"fetch_results_{year}.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(year_results, f, ensure_ascii=False, indent=2)
        print(f"结果已保存: {results_file}")

    # 汇总
    print(f"\n{'='*60}")
    print("下载结果汇总:")
    downloaded = sum(1 for yr in all_results.values() for v in yr.values() if v["status"] == "downloaded")
    exists = sum(1 for yr in all_results.values() for v in yr.values() if v["status"] == "exists")
    not_found = sum(1 for yr in all_results.values() for v in yr.values() if v["status"] == "not_found")
    failed = sum(1 for yr in all_results.values() for v in yr.values() if v["status"] not in ("downloaded", "exists", "not_found"))

    print(f"  成功下载: {downloaded}")
    print(f"  文件已存在: {exists}")
    print(f"  未找到: {not_found}")
    print(f"  失败: {failed}")

    # 列出所有 PDF
    pdfs = list(DOWNLOADS_DIR.glob("*.pdf"))
    print(f"\n当前目录已有 PDF ({len(pdfs)} 个):")
    for pdf in sorted(pdfs):
        print(f"  {pdf.name} ({pdf.stat().st_size // 1024}KB)")


if __name__ == "__main__":
    main()
