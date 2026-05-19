#!/usr/bin/env python3
"""从正确年报 PDF 提取飞机日利用率"""
import pdfplumber, re, os, json

CORRECT_DIR = "/Users/fox/Claude Code/data-analysis-local/airline-annual-reports/downloads/correct"
OUTPUT_FILE = "/Users/fox/Claude Code/data-analysis-local/airline-annual-reports/parsed/utilization_correct.json"
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

airlines = ["春秋航空", "吉祥航空", "中国国航", "中国东航", "南方航空", "海航控股", "华夏航空"]

def extract_utilization(filepath, airline, fy):
    result = {
        "airline": airline, "fiscal_year": fy,
        "飞机日利用率": None, "数据来源页": None,
        "原始文本": None, "运营数据期": None,
        "全部候选": []
    }
    try:
        with pdfplumber.open(filepath) as pdf:
            result["总页数"] = len(pdf.pages)
            candidates = []
            
            for i in range(min(len(pdf.pages), 250)):
                page = pdf.pages[i]
                text = page.extract_text() or ""
                if not text.strip():
                    continue
                page_num = i + 1
                
                for line in text.split('\n'):
                    line_stripped = line.strip()
                    if not line_stripped or len(line_stripped) < 5:
                        continue
                    
                    has_util_kw = any(kw in line_stripped for kw in ["利用率", "利用小时", "日利用", "飞机日利用"])
                    if not has_util_kw:
                        continue
                    
                    nums = re.findall(r'(\d+\.?\d*)', line_stripped)
                    for num_str in nums:
                        try:
                            val = float(num_str)
                            if not (3 <= val <= 16):
                                continue
                            
                            if '飞机日利用率' in line_stripped or '飞机日平均利用率' in line_stripped:
                                priority = 4
                            elif '日利用率' in line_stripped and ('飞机' in line_stripped or '在册' in line_stripped or '可用' in line_stripped):
                                priority = 3
                            elif '利用小时' in line_stripped:
                                priority = 2
                            else:
                                priority = 1
                            
                            # 判断数据期
                            period = None
                            if f'{fy}年全' in line_stripped or f'{fy}年度' in line_stripped:
                                period = f"FY{fy}全年"
                            elif f'1至12月' in line_stripped or '全年' in line_stripped:
                                period = "FY全年"
                            elif '1至6月' in line_stripped:
                                period = "H1"
                            elif '7至12月' in line_stripped:
                                period = "H2"
                            
                            candidates.append({
                                "priority": priority, "val": val,
                                "page": page_num, "line": line_stripped[:250],
                                "period": period
                            })
                        except:
                            pass
                
                # 表格
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if not row:
                            continue
                        row_text = ' | '.join([str(c) if c else '' for c in row])
                        if '利用率' not in row_text and '利用小时' not in row_text:
                            continue
                        cols = len(row)
                        for idx, cell in enumerate(row):
                            if not cell:
                                continue
                            cell_str = str(cell).strip()
                            # 查找数值格
                            if cell_str.replace('.','').replace(',','').isdigit():
                                try:
                                    val = float(cell_str.replace(',',''))
                                    if 3 <= val <= 16:
                                        # 判断是否在"利用率"行
                                        priority = 4 if '飞机日利用率' in row_text else 3
                                        candidates.append({
                                            "priority": priority, "val": val,
                                            "page": page_num,
                                            "line": row_text[:250],
                                            "period": None,
                                            "source": "table"
                                        })
                                except:
                                    pass
                            # 检查关键词格旁的数值
                            elif any(kw in cell_str for kw in ["利用率", "利用小时"]):
                                for other in row:
                                    if other and other != cell:
                                        try:
                                            val = float(str(other).strip().replace(',',''))
                                            if 3 <= val <= 16:
                                                priority = 4 if '飞机日利用率' in row_text else 3
                                                candidates.append({
                                                    "priority": priority, "val": val,
                                                    "page": page_num,
                                                    "line": row_text[:250],
                                                    "period": None,
                                                    "source": "table_adj"
                                                })
                                        except:
                                            pass
    except Exception as e:
        result["error"] = str(e)
        return result
    
    if candidates:
        candidates.sort(key=lambda x: (-x['priority'], -x['val']))
        best = candidates[0]
        result["飞机日利用率"] = best['val']
        result["数据来源页"] = best['page']
        result["原始文本"] = best['line']
        result["运营数据期"] = best.get('period')
        result["全部候选"] = [
            {"val": c['val'], "prio": c['priority'], "page": c['page'], "period": c.get('period'), "line": c['line'][:120]}
            for c in candidates[:8]
        ]
    
    return result

all_results = []
for airline in airlines:
    for fy in [2023, 2024, 2025]:
        filename = f"{airline}_FY{fy}_年报.pdf"
        filepath = os.path.join(CORRECT_DIR, filename)
        if not os.path.exists(filepath):
            print(f"⛔ {airline} FY{fy}: 不存在")
            continue
        print(f"→ {airline} FY{fy}...", end=" ", flush=True)
        r = extract_utilization(filepath, airline, fy)
        val = r.get('飞机日利用率')
        page = r.get('数据来源页')
        period = r.get('运营数据期', '?')
        print(f"{'✓' if val else '✗'} {val or '未找到'}h/d (p{page}, {period})")
        if val and r.get('全部候选'):
            for c in r['全部候选'][:3]:
                print(f"   候选: {c['val']}h/d p{c['page']} [{c['line'][:80]}]")
        all_results.append(r)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)
print(f"\n已保存: {OUTPUT_FILE}")
