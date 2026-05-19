#!/usr/bin/env python3
"""
Robust airline annual report PDF parser v2.
Handles varied layouts, units, and naming conventions.
"""
import pdfplumber, re, os, sqlite3, json
from pathlib import Path

BASE_DIR = "/Users/fox/Claude Code/data-analysis-local/airline-annual-reports"
DOWNLOAD_DIR = f"{BASE_DIR}/downloads"
DB_PATH = "/Users/fox/DB/external_data.db"

# Extended name matching - try multiple variants
AIRLINE_NAMES = {
    '春秋航空': ['春秋航空', '春秋航空股份有限公司'],
    '吉祥航空': ['吉祥航空', '上海吉祥航空股份有限公司'],
    '中国国航': ['中国国际航空', '中国国际航空股份有限公司', '中国国航'],
    '中国东航': ['中国东方航空', '中国东方航空股份有限公司', '中国东航', '东方航空'],
    '南方航空': ['中国南方航空', '中国南方航空股份有限公司', '南方航空', '南航'],
    '海航控股': ['海南航空', '海航控股', '海南航空控股', '海航'],
    '华夏航空': ['华夏航空', '华夏航空股份有限公司'],
}

STOCK_CODES = {
    '春秋航空': '601021',
    '吉祥航空': '603885',
    '中国国航': '601111',
    '中国东航': '600115',
    '南方航空': '600029',
    '海航控股': '600221',
    '华夏航空': None,
}

PDF_FILES = [
    '春秋航空_2023_年度报告.pdf',
    '春秋航空_2024_年度报告.pdf',
    '春秋航空_2025_年度报告.pdf',
    '吉祥航空_2023_年度报告.pdf',
    '吉祥航空_2024_年度报告.pdf',
    '吉祥航空_2025_年度报告.pdf',
    '中国国航_2023_年度报告.pdf',
    '中国国航_2024_年度报告.pdf',
    '中国国航_2025_年度报告.pdf',
    '中国东航_2023_年度报告.pdf',
    '中国东航_2024_年度报告.pdf',
    '中国东航_2025_年度报告.pdf',
    '南方航空_2023_年度报告.pdf',
    '南方航空_2024_年度报告.pdf',
    '南方航空_2025_年度报告.pdf',
    '海航控股_2023_年度报告.pdf',
    '海航控股_2024_年度报告.pdf',
    '海航控股_2025_年度报告.pdf',
    '华夏航空_2023_年度报告.pdf',
    '华夏航空_2024_年度报告.pdf',
    '华夏航空_2025_年度报告.pdf',
]

def parse_number(s):
    """Parse a number string, return None if not valid"""
    if s is None:
        return None
    s = str(s).strip()
    if not s or s in ['不适用', '-', '—', 'None', '', 'nan']:
        return None
    s = s.replace(',', '').replace(' ', '').replace('%', '').replace('元', '').replace('美元', '')
    # Handle parentheses for negative numbers
    if s.startswith('(') and s.endswith(')'):
        s = '-' + s[1:-1]
    try:
        return float(s)
    except:
        return None

def parse_yoy(s):
    """Parse YoY value from various formats"""
    if s is None:
        return None
    s = str(s).strip()
    if not s or s in ['不适用', '-', '—', 'None', '', 'nan']:
        return None
    # Handle parentheses for negative: (49.65%) -> -49.65
    if s.startswith('(') and s.endswith(')'):
        s = '-' + s[1:-1]
    s = s.replace('%', '').replace(',', '')
    # Handle "增加/减少 XX" or "增加XX"
    m = re.search(r'增加\s*[/\s]*\s*减少\s*(\d+\.?\d*)', s)
    if m:
        return -abs(parse_number(m.group(1)))
    m = re.search(r'[增加上升](\d+\.?\d*)', s)
    if m:
        return parse_number(m.group(1))
    m = re.search(r'[下降减少](\d+\.?\d*)', s)
    if m:
        return -abs(parse_number(m.group(1)))
    try:
        return float(s)
    except:
        return None

def clean_text(text):
    if not text:
        return ''
    return re.sub(r'[\n\r]+', '\n', text)

def determine_airline_name(text):
    """Determine airline name from page text"""
    text_first_lines = '\n'.join(text.split('\n')[:5])
    for standard_name, variants in AIRLINE_NAMES.items():
        for variant in variants:
            if variant in text_first_lines:
                return standard_name
    return None

def determine_report_type(pdf):
    """Scan first 3 pages to determine report type"""
    for i in range(min(3, len(pdf.pages))):
        text = pdf.pages[i].extract_text() or ''
        if '半年度报告' in text or '半年度' in text[:200]:
            return 'semi'
        if '年度报告' in text:
            return 'annual'
    return 'annual'

def extract_year_from_filename(filename):
    m = re.search(r'_(\d{4})_', filename)
    if m:
        return int(m.group(1))
    return None

def find_ops_data_pages(pdf, airline_name):
    """Find all pages with operational data for a given airline"""
    ops_pages = []
    search_keywords = ['可用座位公里', '可用座公里', 'ASK', '可用座公里数']
    
    for i in range(min(30, len(pdf.pages))):
        text = clean_text(pdf.pages[i].extract_text() or '')
        if any(kw in text for kw in search_keywords):
            ops_pages.append(i)
    return ops_pages

def extract_single_number_from_line(line, label):
    """Extract a single number following a label in a line"""
    # Pattern: label number
    patterns = [
        rf'{re.escape(label)}[（(][^）)]*[）)]\s*([0-9,\.]+)',
        rf'{re.escape(label)}\s*[：:\s]*([0-9,\.\-]+)',
        rf'{re.escape(label)}\s*\n\s*([0-9,\.\-]+)',
    ]
    for pat in patterns:
        m = re.search(pat, line)
        if m:
            return parse_number(m.group(1))
    return None

def find_yoy_after_label(lines, label_pattern, max_lines=3):
    """Find YoY percentage after a label in nearby lines"""
    for i, line in enumerate(lines):
        if re.search(label_pattern, line):
            # Check this line and next few for YoY
            for j in range(i, min(i+max_lines, len(lines))):
                l = lines[j]
                # Match patterns like "128.09%" or "(49.65%)" or "增加15.34个百分点"
                m = re.search(r'\(?([0-9]+\.[0-9]+)\s*%?\)?', l)
                if m:
                    return parse_yoy(m.group(1))
                # Check for percentage with symbol
                m2 = re.search(r'([0-9]+\.[0-9]+)%', l)
                if m2:
                    return parse_yoy(m2.group(1))
    return None

def extract_ops_data_v2(text, page_idx, pdf):
    """Extract operational data from text using table-aware parsing"""
    data = {}
    text = clean_text(text)
    lines = text.split('\n')
    
    # Detect unit for ASK: 万人公里, 万公里, 百万公里
    # Check first occurrence of ASK value
    ask_unit = None
    for line in lines:
        if '可用座位公里' in line or '可用座公里' in line:
            if '百万' in line or '（百万' in line:
                ask_unit = '百万'
            elif '万' in line:
                # Check if it's 万人公里
                if '万人公里' in line:
                    ask_unit = '万人公里'
                else:
                    ask_unit = '万公里'
            break
    
    # Extract ASK
    for i, line in enumerate(lines):
        if '可用座位公里' in line or ('可用座公里' in line and '可用座公里数' in line):
            # Next line typically has the value
            for j in range(i, min(i+3, len(lines))):
                l = lines[j].strip()
                if not l:
                    continue
                # Find numbers in this line
                nums = re.findall(r'([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)', l)
                if nums:
                    # Skip percentages and small numbers
                    for num_str in nums:
                        num = parse_number(num_str)
                        if num and num > 100:  # Reasonable for ASK
                            data['ask_value'] = num
                            data['ask_unit'] = ask_unit
                            break
                    if 'ask_value' in data:
                        break
    
    # Extract RPK
    for i, line in enumerate(lines):
        if '旅客周转量' in line and 'RPK' in line:
            for j in range(i, min(i+3, len(lines))):
                l = lines[j].strip()
                if not l:
                    continue
                nums = re.findall(r'([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)', l)
                for num_str in nums:
                    num = parse_number(num_str)
                    if num and num > 100:
                        data['rpk_value'] = num
                        break
                if 'rpk_value' in data:
                    break
    
    # Extract PLF (客座率)
    for i, line in enumerate(lines):
        if '客座率' in line or '平均客座率' in line:
            # Look for percentage value
            m = re.search(r'([0-9]+\.[0-9]+)\s*%', line)
            if m:
                data['plf'] = parse_number(m.group(1))
            # Also look for it on next line
            if 'plf' not in data and i+1 < len(lines):
                m = re.search(r'([0-9]+\.[0-9]+)\s*%', lines[i+1])
                if m:
                    data['plf'] = parse_number(m.group(1))
    
    # Extract YoY for ASK - look for percentage near the ASK section
    for i, line in enumerate(lines):
        if ('可用座位公里' in line or '可用座公里' in line) and i+1 < len(lines):
            # Check next few lines for YoY percentage
            for j in range(i, min(i+4, len(lines))):
                l = lines[j]
                # Match 128.09% style
                m = re.search(r'([0-9]+\.[0-9]+)\s*%', l)
                if m:
                    data['ask_yoy'] = parse_yoy(m.group(1))
                    break
                # Match (49.65%) style for negative
                m2 = re.search(r'\(([0-9]+\.[0-9]+)\s*%\)', l)
                if m2:
                    data['ask_yoy'] = parse_yoy('-' + m2.group(1))
                    break
            if 'ask_yoy' in data:
                break
    
    # Extract YoY for RPK
    for i, line in enumerate(lines):
        if '旅客周转量' in line:
            for j in range(i, min(i+4, len(lines))):
                l = lines[j]
                m = re.search(r'([0-9]+\.[0-9]+)\s*%', l)
                if m:
                    data['rpk_yoy'] = parse_yoy(m.group(1))
                    break
                m2 = re.search(r'\(([0-9]+\.[0-9]+)\s*%\)', l)
                if m2:
                    data['rpk_yoy'] = parse_yoy('-' + m2.group(1))
                    break
            if 'rpk_yoy' in data:
                break
    
    # Extract PLF YoY (百分点变化)
    for i, line in enumerate(lines):
        if '客座率' in line or '平均客座率' in line:
            m = re.search(r'[增加上升下降减少]+(\d+\.?\d*)\s*个百分点', line)
            if m:
                val = parse_number(m.group(1))
                if '下降' in line or '减少' in line:
                    val = -val
                data['plf_yoy'] = val
    
    # Extract passengers (万人次)
    for i, line in enumerate(lines):
        if '旅客运输量' in line or '载运旅客人次' in line:
            nums = re.findall(r'([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)', line)
            for num_str in nums:
                num = parse_number(num_str)
                if num and num > 10:  # Reasonable for passengers in 万
                    data['passengers'] = num
                    break
            if 'passengers' in data:
                break
    
    # Extract fleet size
    for i, line in enumerate(lines):
        if '机队' in line and ('架' in line or '架次' in line):
            m = re.search(r'(\d+)\s*架', line)
            if m:
                val = int(m.group(1))
                if 10 < val < 2000:  # Reasonable fleet size
                    data['fleet_size'] = val
    
    return data

def convert_to_billion(value, unit):
    """Convert ASK/RPK values to 亿元 (billion yuan equivalent units)"""
    if value is None:
        return None
    if unit is None:
        return value  # Assume already in 亿元
    
    if unit == '万人公里':
        # 万人公里 / 10000 = 亿元-公里
        return value / 10000.0
    elif unit == '万公里':
        # 万公里 / 10000 = 亿元-公里  
        return value / 10000.0
    elif unit == '百万':
        # 百万公里 * 100 = 亿元-公里 (1百万 = 100万, 1万 = 10000, so 1百万 = 100 * 10000 = 1,000,000)
        # Actually: 1百万公里 = 1,000,000 公里, and we want 亿元-km
        # 1亿元 = 100,000,000, so 1百万公里 = 0.01 亿元-km? No that's wrong.
        # Let me reconsider: we're storing passenger-km in "亿元 equivalent units"
        # 1 万人公里 = 10,000 passenger-km = 元/10 if we treat as currency
        # 1 百万公里 = 1,000,000 passenger-km = 元/0.1 if treated as currency
        # The task says "divide by 10000 from 万人公里" to get 亿元
        # For 百万: 1百万 = 100万 = 100 * 1万, so 百万公里 / 10000 * 100 = 百万/100
        return value * 100.0 / 10000.0  # = value / 100
        # Wait: 1百万 = 100万, and 1万km in 亿元 = /10000
        # So 1百万km = 100万km = 100 * (万km in 亿元) * 10000... confusing.
        # Let me think again:
        # value_in_亿元 = value_in_万人公里 / 10000
        # For 百万公里: 1百万公里 = 100万km
        # value_in_亿元 = 100万km / 10000 = 100/10000 * 百万 = 0.01 * 百万
        return value * 0.01
    else:
        return value

def extract_financial_data_v2(pdf, report_type='semi'):
    """Extract financial data - revenue, net profit, assets, etc."""
    fin_data = {}
    
    start_page = 50 if report_type == 'semi' else 59
    end_page = min(75, len(pdf.pages))
    
    for i in range(start_page, end_page):
        text = clean_text(pdf.pages[i].extract_text() or '')
        lines = text.split('\n')
        
        # Revenue (营业收入) - need to find in profit table section
        # Skip if this looks like a segment table (has complex structure)
        if '营业收入' in text:
            # Find the line with 营业收入 and a large number
            for j, line in enumerate(lines):
                if '营业收入' in line and '营业成本' not in line[:50]:
                    # Look for number in this or next line
                    for k in range(j, min(j+2, len(lines))):
                        l = lines[k]
                        nums = re.findall(r'([0-9]{1,3}(?:,[0-9]{3})+)', l)
                        for num_str in nums:
                            val = parse_number(num_str)
                            if val and val > 1000000:  # 元
                                fin_data['revenue'] = val / 1e8  # Convert to 亿元
                                break
                    if 'revenue' in fin_data:
                        break
            if 'revenue' in fin_data:
                break
        
        # Net profit (净利润) - in profit table
        if '净利润' in text and '归属' not in text[:100]:
            for j, line in enumerate(lines):
                if '净利润' in line:
                    for k in range(j, min(j+2, len(lines))):
                        l = lines[k]
                        nums = re.findall(r'([0-9]{1,3}(?:,[0-9]{3})+)', l)
                        for num_str in nums:
                            val = parse_number(num_str)
                            if val and abs(val) > 100000:  # 元
                                fin_data['net_profit'] = val / 1e8
                                break
                    if 'net_profit' in fin_data:
                        break
            if 'net_profit' in fin_data:
                break
        
        # Total assets (资产总计)
        if '资产总计' in text:
            for j, line in enumerate(lines):
                if '资产总计' in line:
                    nums = re.findall(r'([0-9]{1,3}(?:,[0-9]{3})+)', line)
                    for num_str in nums:
                        val = parse_number(num_str)
                        if val and val > 1000000:
                            fin_data['total_assets'] = val / 1e8
                            break
            if 'total_assets' in fin_data:
                break
        
        # Net assets (所有者权益)
        if '所有者权益' in text or '股东权益' in text:
            for j, line in enumerate(lines):
                if ('所有者权益' in line or '股东权益' in line) and '合计' in line:
                    nums = re.findall(r'([0-9]{1,3}(?:,[0-9]{3})+)', line)
                    for num_str in nums:
                        val = parse_number(num_str)
                        if val and val > 1000000:
                            fin_data['net_assets'] = val / 1e8
                            break
            if 'net_assets' in fin_data:
                break
        
        # Asset-liability ratio
        if '资产负债率' in text:
            m = re.search(r'资产负债率[：:\s]*([0-9]+\.?[0-9]*)', text)
            if m:
                fin_data['asset_liability_ratio'] = parse_number(m.group(1))
        
        # EPS
        if '每股收益' in text:
            m = re.search(r'基本每股收益[：:\s]*([0-9]+\.?[0-9]*)', text)
            if m:
                fin_data['eps'] = parse_number(m.group(1))
        
        # ROE - look for 加权平均净资产收益率
        if '加权平均净资产收益率' in text or '加权平均' in text:
            m = re.search(r'加权平均净资产收益率[：:\s]*([0-9]+\.?[0-9]*)', text)
            if m:
                fin_data['roe'] = parse_number(m.group(1))
    
    return fin_data

def parse_single_pdf_v2(filepath):
    """Parse a single PDF with improved logic"""
    filename = os.path.basename(filepath)
    print(f"\n{'='*60}")
    print(f"Parsing: {filename}")
    
    data = {
        'airline_name': None,
        'stock_code': None,
        'report_year': None,
        'report_type': None,
        'ask_billion': None,
        'rpk_billion': None,
        'ask_yoy': None,
        'rpk_yoy': None,
        'passenger_load_factor': None,
        'domestic_ask_yoy': None,
        'international_ask_yoy': None,
        'regional_ask_yoy': None,
        'domestic_plf': None,
        'international_plf': None,
        'regional_plf': None,
        'revenue': None,
        'net_profit': None,
        'total_assets': None,
        'net_assets': None,
        'asset_liability_ratio': None,
        'roe': None,
        'eps': None,
        'passengers_million': None,
        'fleet_size': None,
        'data_source': 'pdf_annual_report',
    }
    
    try:
        with pdfplumber.open(filepath) as pdf:
            total_pages = len(pdf.pages)
            print(f"  Total pages: {total_pages}")
            
            # 1. Determine report type and airline name
            data['report_type'] = determine_report_type(pdf)
            first_page_text = clean_text(pdf.pages[0].extract_text() or '')
            data['airline_name'] = determine_airline_name(first_page_text)
            data['report_year'] = extract_year_from_filename(filename)
            data['stock_code'] = STOCK_CODES.get(data['airline_name'])
            
            print(f"  Airline: {data['airline_name']}, Year: {data['report_year']}, "
                  f"Type: {data['report_type']}, Stock: {data['stock_code']}")
            
            if not data['airline_name']:
                print(f"  ERROR: Could not identify airline!")
                return data, filename
            
            # 2. Find and parse operational data
            ops_pages = find_ops_data_pages(pdf, data['airline_name'])
            print(f"  Ops data pages found: {[p+1 for p in ops_pages]}")
            
            for ops_idx in ops_pages:
                ops_text = clean_text(pdf.pages[ops_idx].extract_text() or '')
                ops_data = extract_ops_data_v2(ops_text, ops_idx, pdf)
                
                if ops_data.get('ask_value'):
                    unit = ops_data.get('ask_unit')
                    data['ask_billion'] = convert_to_billion(ops_data['ask_value'], unit)
                
                if ops_data.get('rpk_value'):
                    unit = ops_data.get('ask_unit')  # Same unit context
                    data['rpk_billion'] = convert_to_billion(ops_data['rpk_value'], unit)
                
                if ops_data.get('ask_yoy') is not None:
                    data['ask_yoy'] = ops_data['ask_yoy']
                if ops_data.get('rpk_yoy') is not None:
                    data['rpk_yoy'] = ops_data['rpk_yoy']
                if ops_data.get('plf') is not None:
                    data['passenger_load_factor'] = ops_data['plf']
                if ops_data.get('plf_yoy') is not None:
                    data['plf_yoy'] = ops_data['plf_yoy']
                if ops_data.get('passengers'):
                    data['passengers_million'] = ops_data['passengers']
                if ops_data.get('fleet_size'):
                    data['fleet_size'] = ops_data['fleet_size']
            
            # 3. Extract financial data
            fin_data = extract_financial_data_v2(pdf, data['report_type'])
            for k, v in fin_data.items():
                if v is not None and k in data:
                    data[k] = v
            
            # 4. Print summary
            print(f"  ASK: {data.get('ask_billion')} 亿元")
            print(f"  RPK: {data.get('rpk_billion')} 亿元")
            print(f"  PLF: {data.get('passenger_load_factor')}%")
            print(f"  ASK YoY: {data.get('ask_yoy')}%")
            print(f"  RPK YoY: {data.get('rpk_yoy')}%")
            print(f"  Passengers: {data.get('passengers_million')} 万")
            print(f"  Fleet: {data.get('fleet_size')} 架")
            print(f"  Revenue: {data.get('revenue')} 亿元")
            print(f"  Net profit: {data.get('net_profit')} 亿元")
            print(f"  Total assets: {data.get('total_assets')} 亿元")
            print(f"  Net assets: {data.get('net_assets')} 亿元")
            print(f"  Asset-liability ratio: {data.get('asset_liability_ratio')}%")
            print(f"  EPS: {data.get('eps')} 元/股")
            print(f"  ROE: {data.get('roe')}%")
    
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    return data, filename

def upsert_to_db(data):
    """Upsert data to SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Build upsert query
    key_fields = ['airline_name', 'report_year', 'report_type']
    data_fields = [k for k in data.keys() if k not in key_fields and data[k] is not None]
    
    columns = key_fields + data_fields
    placeholders = ', '.join(['?' for _ in columns])
    update_parts = [f"{k}=excluded.{k}" for k in data_fields]
    
    query = f"""
    INSERT INTO airline_annual_report 
    ({', '.join(columns)})
    VALUES ({placeholders})
    ON CONFLICT(airline_name, report_year, report_type) 
    DO UPDATE SET {', '.join(update_parts)}
    """
    
    values = [data[k] for k in columns]
    cursor.execute(query, values)
    conn.commit()
    rows = cursor.rowcount
    cursor.close()
    conn.close()
    return rows

def main():
    print("=" * 60)
    print("AIRLINE ANNUAL REPORT PDF PARSER v2")
    print("=" * 60)
    
    all_results = []
    
    for filename in PDF_FILES:
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        if not os.path.exists(filepath):
            print(f"\n⛔ File not found: {filename}")
            continue
        
        data, fname = parse_single_pdf_v2(filepath)
        all_results.append({'filename': fname, 'data': data})
        
        # Upsert to database
        if data['airline_name'] and data['report_year'] and data['report_type']:
            rows = upsert_to_db(data)
            print(f"  ✓ Upserted to DB (rows: {rows})")
        else:
            print(f"  ✗ Skipped DB - missing key fields")
    
    # Save results
    output_file = f"{BASE_DIR}/parsed/all_pdf_parsed_results_v2.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {output_file}")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for r in all_results:
        d = r['data']
        if d['ask_billion']:
            status = "OK"
        elif d['revenue']:
            status = "PARTIAL"
        else:
            status = "LOW"
        print(f"  {d['airline_name']} {d['report_year']} ({d['report_type']}): {status} "
              f"| ASK={d['ask_billion']} | PLF={d['passenger_load_factor']} | "
              f"Rev={d['revenue']} | Profit={d['net_profit']}")

if __name__ == '__main__':
    main()