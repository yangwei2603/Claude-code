#!/usr/bin/env python3
"""
Comprehensive extraction of financial and operational metrics from Chinese airline annual reports.
Uses table parsing for better accuracy.
"""
import pdfplumber, re, os, json, sqlite3
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path("/Users/fox/Claude Code/data-analysis-local/airline-annual-reports")
DOWNLOAD_DIR = BASE_DIR / "downloads" / "correct"
DB_PATH = "/Users/fox/DB/external_data.db"
OUTPUT_FILE = BASE_DIR / "parsed" / "all_metrics_extracted.json"

os.makedirs(BASE_DIR / "parsed", exist_ok=True)

# Airline mapping
AIRLINES = {
    "春秋航空": {"stock_code": "601021", "files": {}},
    "吉祥航空": {"stock_code": "603885", "files": {}},
    "中国国航": {"stock_code": "601111", "files": {}},
    "中国东航": {"stock_code": "600115", "files": {}},
    "南方航空": {"stock_code": "600029", "files": {}},
    "海航控股": {"stock_code": "600221", "files": {}},
    "华夏航空": {"stock_code": "002928", "files": {}},
}

# Find PDF files
for airline in AIRLINES:
    for year in [2023, 2024, 2025]:
        for pattern in [
            f"{airline}_FY{year}_年报.pdf",
            f"{airline}_{year}_年度报告.pdf",
        ]:
            filepath = DOWNLOAD_DIR / pattern
            if filepath.exists():
                AIRLINES[airline]["files"][year] = str(filepath)
                break

def clean_num_str(s):
    """Clean a number string - remove commas, spaces, etc."""
    if s is None:
        return None
    s = str(s).strip().replace(',', '').replace('，', '').replace(' ', '')
    if not s or s == '-' or s == '不适用':
        return None
    return s

def parse_number(s, unit=1.0):
    """Parse number string with optional unit multiplier"""
    s = clean_num_str(s)
    if s is None:
        return None
    # Handle percentages
    if '%' in s:
        s = s.replace('%', '')
    # Handle parentheses for negative numbers
    if '(' in s and ')' in s:
        s = '-' + s.replace('(', '').replace(')', '')
    try:
        val = float(s)
        return val * unit
    except:
        return None

def extract_from_table_row(row, label_keywords, value_index=1, unit=1.0):
    """Extract value from a table row based on label keywords"""
    for i, cell in enumerate(row):
        if cell and isinstance(cell, str):
            if any(kw in cell for kw in label_keywords):
                # Try to get value from the cell after label
                if value_index + i < len(row):
                    val = parse_number(row[value_index + i], unit)
                    if val is not None:
                        return val
                # Or try to get from the next column
                if i + 1 < len(row):
                    val = parse_number(row[i + 1], unit)
                    if val is not None:
                        return val
    return None

def scan_pdf_pages(filepath):
    """Scan PDF and extract all metrics from tables"""
    metrics = {}
    
    try:
        with pdfplumber.open(filepath) as pdf:
            total_pages = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                text = (page.extract_text() or "").replace('\n', ' ')
                
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    
                    # Flatten table for searching
                    table_text = ' '.join([str(c) if c else '' for row in table for c in row])
                    
                    # ==== Financial Data Table (通常在"主要会计数据"页面) ====
                    # Revenue - 营业收入
                    if '营业收入' in table_text and len(table) > 1:
                        for row in table:
                            row_text = ' '.join([str(c) if c else '' for c in row])
                            if '营业收入' in row_text and len(row) >= 2:
                                for i, cell in enumerate(row):
                                    if cell and '营业收入' in str(cell) and i + 1 < len(row):
                                        val = parse_number(row[i + 1], 1e-8)  # Convert 元 to 亿元
                                        if val and val > 10:  # Should be > 10 billion
                                            metrics['revenue'] = val
                                        # Also check YoY
                                        if i + 2 < len(row):
                                            yoy = parse_number(row[i + 2])
                                            if yoy and abs(yoy) < 500:
                                                metrics['revenue_yoy'] = yoy
                    
                    # Net Profit - 净利润
                    if any(kw in table_text for kw in ['归属于上市公司股东的净利润', '归母净利润']):
                        for row in table:
                            row_text = ' '.join([str(c) if c else '' for c in row])
                            if any(kw in row_text for kw in ['归属于上市公司股东的净利润', '归母净利润']):
                                for i, cell in enumerate(row):
                                    if cell and any(kw in str(cell) for kw in ['归属于上市公司股东的净利润', '归母净利润']) and i + 1 < len(row):
                                        val = parse_number(row[i + 1], 1e-8)
                                        if val:
                                            metrics['net_profit'] = val
                                        if i + 2 < len(row):
                                            yoy = parse_number(row[i + 2])
                                            if yoy and abs(yoy) < 500:
                                                metrics['net_profit_yoy'] = yoy
                    
                    # Deducted Net Profit - 扣非净利润
                    if '扣除非经常性损益' in table_text:
                        for row in table:
                            row_text = ' '.join([str(c) if c else '' for c in row])
                            if '扣除非经常性损益' in row_text:
                                for i, cell in enumerate(row):
                                    if cell and '扣除非经常性损益' in str(cell) and i + 1 < len(row):
                                        val = parse_number(row[i + 1], 1e-8)
                                        if val:
                                            metrics['deducted_net_profit'] = val
                    
                    # Total Assets - 总资产
                    if '总资产' in table_text or '资产总计' in table_text:
                        for row in table:
                            row_text = ' '.join([str(c) if c else '' for c in row])
                            if ('总资产' in row_text or '资产总计' in row_text) and len(row) >= 2:
                                for i, cell in enumerate(row):
                                    if cell and str(cell).strip() in ['总资产', '资产总计'] and i + 1 < len(row):
                                        val = parse_number(row[i + 1], 1e-8)
                                        if val and val > 100:
                                            metrics['total_assets'] = val
                    
                    # Net Assets - 净资产
                    if '归属于上市公司股东的净资产' in table_text or '归母净资产' in table_text:
                        for row in table:
                            row_text = ' '.join([str(c) if c else '' for c in row])
                            if '归属于上市公司股东的净资产' in row_text or '归母净资产' in row_text:
                                for i, cell in enumerate(row):
                                    if cell and ('归属于上市公司股东的净资产' in str(cell) or '归母净资产' in str(cell)) and i + 1 < len(row):
                                        val = parse_number(row[i + 1], 1e-8)
                                        if val and val > 10:
                                            metrics['net_assets'] = val
                    
                    # Asset Liability Ratio - 资产负债率
                    if '资产负债率' in table_text:
                        for row in table:
                            row_text = ' '.join([str(c) if c else '' for c in row])
                            if '资产负债率' in row_text:
                                for i, cell in enumerate(row):
                                    if cell and '资产负债率' in str(cell) and i + 1 < len(row):
                                        val = parse_number(row[i + 1])
                                        if val and 0 < val <= 100:
                                            metrics['asset_liability_ratio'] = val
                    
                    # Gross Margin - 毛利率
                    if '毛利率' in table_text:
                        for row in table:
                            row_text = ' '.join([str(c) if c else '' for c in row])
                            if '毛利率' in row_text and len(row) >= 2:
                                for i, cell in enumerate(row):
                                    if cell and '毛利率' in str(cell) and i + 1 < len(row):
                                        val = parse_number(row[i + 1])
                                        if val and 0 < val < 100:
                                            metrics['gross_margin'] = val
                    
                    # Operating Cash Flow - 经营现金流
                    if '经营活动产生的现金流量净额' in table_text or '经营现金流' in table_text:
                        for row in table:
                            row_text = ' '.join([str(c) if c else '' for c in row])
                            if '经营活动产生的现金流量净额' in row_text or '经营现金流' in row_text:
                                for i, cell in enumerate(row):
                                    if cell and ('经营活动产生的现金流量净额' in str(cell) or '经营现金流' in str(cell)) and i + 1 < len(row):
                                        val = parse_number(row[i + 1], 1e-8)
                                        if val:
                                            metrics['operating_cash_flow'] = val
                    
                    # EPS - 每股收益
                    if '每股收益' in table_text or '基本每股收益' in table_text:
                        for row in table:
                            row_text = ' '.join([str(c) if c else '' for c in row])
                            if '基本每股收益' in row_text or ('每股收益' in row_text and '稀释' not in row_text):
                                for i, cell in enumerate(row):
                                    if cell and '基本每股收益' in str(cell) and i + 1 < len(row):
                                        val = parse_number(row[i + 1])
                                        if val and abs(val) < 100:
                                            metrics['eps'] = val
                    
                    # ROE - 净资产收益率
                    if '净资产收益率' in table_text or '加权平均净资产收益率' in table_text:
                        for row in table:
                            row_text = ' '.join([str(c) if c else '' for c in row])
                            if '加权平均净资产收益率' in row_text or '净资产收益率' in row_text:
                                for i, cell in enumerate(row):
                                    if cell and '加权平均净资产收益率' in str(cell) and i + 1 < len(row):
                                        val = parse_number(row[i + 1])
                                        if val and 0 < abs(val) < 100:
                                            metrics['roe'] = val
                    
                    # ==== Operational Data Tables ====
                    # Passengers - 旅客运输量
                    if '旅客运输量' in table_text or '旅客周转量' in table_text:
                        for row in table:
                            row_text = ' '.join([str(c) if c else '' for c in row])
                            if '旅客运输量' in row_text and len(row) >= 2:
                                for i, cell in enumerate(row):
                                    if cell and '旅客运输量' in str(cell) and i + 1 < len(row):
                                        val = parse_number(row[i + 1])
                                        if val and val > 1:
                                            metrics['passengers_million'] = val / 100  # Convert 万 to million
                                        # Check for YoY in subsequent column
                                        if i + 2 < len(row):
                                            yoy = parse_number(row[i + 2])
                                            if yoy and abs(yoy) < 500:
                                                metrics['passengers_yoy'] = yoy
                    
                    # ASK - 可用座位公里
                    if '可用座位公里' in table_text or '可用座公里' in table_text or 'ASK' in table_text.upper():
                        for row in table:
                            row_text = ' '.join([str(c) if c else '' for c in row])
                            if '可用座位公里' in row_text or '可用座公里' in row_text or 'ASK' in row_text.upper():
                                for i, cell in enumerate(row):
                                    if cell and ('可用座位公里' in str(cell) or '可用座公里' in str(cell) or 'ASK' in str(cell).upper()) and i + 1 < len(row):
                                        val = parse_number(row[i + 1])
                                        if val and val > 1:
                                            metrics['ask_billion'] = val  # Assumed in 亿
                                        if i + 2 < len(row):
                                            yoy = parse_number(row[i + 2])
                                            if yoy and abs(yoy) < 500:
                                                metrics['ask_yoy'] = yoy
                    
                    # RPK - 收入客公里
                    if '收入客公里' in table_text or '旅客周转量' in table_text or 'RPK' in table_text.upper():
                        for row in table:
                            row_text = ' '.join([str(c) if c else '' for c in row])
                            if '收入客公里' in row_text or '旅客周转量' in row_text or 'RPK' in row_text.upper():
                                for i, cell in enumerate(row):
                                    if cell and ('收入客公里' in str(cell) or '旅客周转量' in str(cell) or 'RPK' in str(cell).upper()) and i + 1 < len(row):
                                        val = parse_number(row[i + 1])
                                        if val and val > 1:
                                            metrics['rpk_billion'] = val
                                        if i + 2 < len(row):
                                            yoy = parse_number(row[i + 2])
                                            if yoy and abs(yoy) < 500:
                                                metrics['rpk_yoy'] = yoy
                    
                    # Passenger Load Factor - 客座率
                    if '客座率' in table_text:
                        for row in table:
                            row_text = ' '.join([str(c) if c else '' for c in row])
                            if '客座率' in row_text and len(row) >= 2:
                                for i, cell in enumerate(row):
                                    if cell and '客座率' in str(cell) and i + 1 < len(row):
                                        val = parse_number(row[i + 1])
                                        if val and 0 < val <= 100:
                                            metrics['passenger_load_factor'] = val
                    
                    # Fleet Size - 机队规模
                    if any(kw in table_text for kw in ['机队', '运输飞机', '飞机总数', '客机', '飞机数量']):
                        for row in table:
                            row_text = ' '.join([str(c) if c else '' for c in row])
                            if any(kw in row_text for kw in ['机队', '运输飞机', '飞机总数', '客机']):
                                for i, cell in enumerate(row):
                                    if cell and any(kw in str(cell) for kw in ['机队', '运输飞机', '飞机总数', '客机']) and i + 1 < len(row):
                                        val = parse_number(row[i + 1])
                                        if val and 10 < val < 2000:
                                            metrics['fleet_size'] = int(val)
                    
                    # Cargo RTK - 货邮周转量
                    if '货邮周转量' in table_text:
                        for row in table:
                            row_text = ' '.join([str(c) if c else '' for c in row])
                            if '货邮周转量' in row_text and len(row) >= 2:
                                for i, cell in enumerate(row):
                                    if cell and '货邮周转量' in str(cell) and i + 1 < len(row):
                                        val = parse_number(row[i + 1])
                                        if val and val > 0:
                                            metrics['cargo_rtk'] = val
                    
                    # ==== Regional Breakdown ====
                    for region in ['国内', '国际', '地区', '港澳台']:
                        region_key = 'domestic' if region == '国内' else ('international' if region == '国际' else 'regional')
                        
                        # Regional PLF
                        if f'{region}' in table_text and '客座率' in table_text:
                            for row in table:
                                row_text = ' '.join([str(c) if c else '' for c in row])
                                if f'{region}' in row_text and '客座率' in row_text:
                                    for i, cell in enumerate(row):
                                        if cell and f'{region}' in str(cell) and i + 1 < len(row):
                                            val = parse_number(row[i + 1])
                                            if val and 0 < val <= 100:
                                                metrics[f'{region_key}_plf'] = val
                    
                    # Exchange Loss - 汇兑损失
                    if '汇兑损失' in table_text or '汇兑损益' in table_text:
                        for row in table:
                            row_text = ' '.join([str(c) if c else '' for c in row])
                            if '汇兑损失' in row_text or '汇兑损益' in row_text:
                                for i, cell in enumerate(row):
                                    if cell and ('汇兑损失' in str(cell) or '汇兑损益' in str(cell)) and i + 1 < len(row):
                                        val = parse_number(row[i + 1], 1e-8)
                                        if val:
                                            metrics['exchange_loss'] = val
                    
                    # Other Income - 其他收益
                    if '其他收益' in table_text:
                        for row in table:
                            row_text = ' '.join([str(c) if c else '' for c in row])
                            if '其他收益' in row_text and len(row) >= 2:
                                for i, cell in enumerate(row):
                                    if cell and '其他收益' in str(cell) and i + 1 < len(row):
                                        val = parse_number(row[i + 1], 1e-8)
                                        if val and val > 0:
                                            metrics['other_income'] = val
                    
                    # Expense Ratios
                    for ratio_name, field in [('财务费用率', 'financial_expense_ratio'), 
                                             ('销售费用率', 'sales_expense_ratio'), 
                                             ('管理费用率', 'management_expense_ratio')]:
                        if ratio_name in table_text:
                            for row in table:
                                row_text = ' '.join([str(c) if c else '' for c in row])
                                if ratio_name in row_text and len(row) >= 2:
                                    for i, cell in enumerate(row):
                                        if cell and ratio_name in str(cell) and i + 1 < len(row):
                                            val = parse_number(row[i + 1])
                                            if val and 0 < val < 50:
                                                metrics[field] = val
                
    except Exception as e:
        print(f"  Error scanning PDF: {e}")
        import traceback
        traceback.print_exc()
    
    return metrics

def upsert_to_database(airline, year, metrics, stock_code):
    """Upsert metrics to database"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Build separate dicts for fields
    set_fields = {}
    for key, value in metrics.items():
        if value is not None:
            set_fields[key] = value
    
    if not set_fields:
        print(f"  No metrics to update for {airline} {year}")
        conn.close()
        return False
    
    # Check if exists
    cur.execute("""
        SELECT id FROM airline_annual_report
        WHERE airline_name = ? AND report_year = ? AND report_type = 'annual'
    """, (airline, year))
    existing = cur.fetchone()
    
    # Build UPDATE SQL
    updates = [f"{k} = ?" for k in set_fields.keys()]
    update_values = list(set_fields.values())
    
    if existing:
        update_sql = f"""
            UPDATE airline_annual_report
            SET {', '.join(updates)},
                data_source = 'PDF extraction'
            WHERE id = ?
        """
        cur.execute(update_sql, update_values + [existing[0]])
        print(f"  [Update] {airline} {year}")
    else:
        all_fields = ['airline_name', 'stock_code', 'report_year', 'report_type', 'data_source'] + list(set_fields.keys())
        all_values = [airline, stock_code, year, 'annual', 'PDF extraction'] + update_values
        insert_sql = f"""
            INSERT INTO airline_annual_report ({', '.join(all_fields)})
            VALUES ({', '.join(['?'] * len(all_values))})
        """
        cur.execute(insert_sql, all_values)
        print(f"  [Insert] {airline} {year}")
    
    conn.commit()
    conn.close()
    return True

def main():
    print("="*70)
    print("Chinese Airline Annual Report - Comprehensive Metrics Extraction v2")
    print("="*70)
    
    all_results = {}
    
    for airline, info in AIRLINES.items():
        print(f"\n>>> {airline} ({info['stock_code']})")
        
        if not info['files']:
            print(f"  No PDF files found")
            continue
        
        for year, filepath in sorted(info['files'].items()):
            print(f"\n  Processing {year}...")
            print(f"    File: {os.path.basename(filepath)}")
            
            metrics = scan_pdf_pages(filepath)
            
            # Count non-null metrics
            found_count = sum(1 for v in metrics.values() if v is not None)
            print(f"    Metrics found: {found_count}/44")
            
            # Show found metrics
            for key, val in sorted(metrics.items()):
                if val is not None:
                    if key in ['revenue', 'net_profit', 'total_assets', 'net_assets', 'operating_cash_flow']:
                        print(f"      {key}: {val:.2f} 亿元")
                    elif key in ['passengers_million']:
                        print(f"      {key}: {val:.2f} 百万人")
                    elif key in ['ask_billion', 'rpk_billion']:
                        print(f"      {key}: {val:.2f} 亿")
                    else:
                        print(f"      {key}: {val}")
            
            # Store result
            all_results[f"{airline}_{year}"] = {
                'airline': airline,
                'year': year,
                'stock_code': info['stock_code'],
                'metrics': metrics,
            }
            
            # Upsert to database
            upsert_to_database(airline, year, metrics, info['stock_code'])
    
    # Save to JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*70}")
    print(f"Extraction complete. Results saved to: {OUTPUT_FILE}")
    print("="*70)

if __name__ == "__main__":
    main()