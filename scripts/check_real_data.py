import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

async def check_real_dragon_tiger_data():
    """检查真实的龙虎榜数据"""
    base_url = "http://data.10jqka.com.cn"
    dragon_tiger_url = f"{base_url}/market/longhu/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # 测试最近的交易日
    test_dates = [
        '2024-12-20',  # 最近的交易日
        '2024-12-19',
        '2024-12-18',
        '2024-12-17',
        '2024-12-16',
    ]
    
    async with aiohttp.ClientSession(headers=headers) as session:
        for trade_date in test_dates:
            print(f"\n=== Checking date: {trade_date} ===")
            
            try:
                url = f"{dragon_tiger_url}?date={trade_date.replace('-', '')}"
                print(f"Request URL: {url}")
                
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"HTTP request failed: {response.status}")
                        continue
                    
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # 查找龙虎榜数据表格
                    dragon_tiger_table = None
                    
                    # 方法1: 查找class为table-hover的表格
                    table_hover = soup.find('table', {'class': 'table-hover'})
                    if table_hover:
                        print("Found table-hover")
                        dragon_tiger_table = table_hover
                    
                    # 方法2: 查找class为m-table的表格
                    if not dragon_tiger_table:
                        m_table = soup.find('table', {'class': 'm-table'})
                        if m_table:
                            print("Found m-table")
                            dragon_tiger_table = m_table
                    
                    # 方法3: 通过表头内容识别
                    if not dragon_tiger_table:
                        tables = soup.find_all('table')
                        for i, table in enumerate(tables):
                            headers = table.find_all('th')
                            if headers and len(headers) >= 6:
                                header_text = ' '.join([th.get_text(strip=True) for th in headers])
                                if any(keyword in header_text for keyword in ['代码', '名称', '涨跌幅', '成交额', '净买入']):
                                    print(f"Found dragon tiger table by headers: Table {i+1}")
                                    dragon_tiger_table = table
                                    break
                    
                    if dragon_tiger_table:
                        print("\n=== Analyzing table data ===")
                        
                        # 获取所有行
                        if dragon_tiger_table.find('tbody'):
                            rows = dragon_tiger_table.find('tbody').find_all('tr')
                            print(f"Found tbody with {len(rows)} rows")
                        else:
                            all_rows = dragon_tiger_table.find_all('tr')
                            print(f"No tbody, found {len(all_rows)} total rows")
                            
                            # 检查第一行是否是表头
                            if all_rows and len(all_rows) > 1:
                                first_row_cells = all_rows[0].find_all(['th', 'td'])
                                first_row_text = ' '.join([cell.get_text(strip=True) for cell in first_row_cells])
                                print(f"First row: {first_row_text}")
                                
                                # 如果第一行包含表头关键词，则跳过第一行
                                if any(keyword in first_row_text for keyword in ['代码', '名称', '涨跌幅', '成交金额']):
                                    rows = all_rows[1:]
                                    print(f"Skipping header row, {len(rows)} data rows remaining")
                                else:
                                    rows = all_rows
                            else:
                                rows = all_rows if all_rows else []
                        
                        print(f"Processing {len(rows)} data rows")
                        
                        # 分析前几行数据
                        found_data = False
                        for i, row in enumerate(rows[:5]):
                            cells = row.find_all(['td', 'th'])
                            if len(cells) < 6:  # 至少需要6列数据
                                print(f"  Row {i+1}: Insufficient columns ({len(cells)})")
                                continue
                            
                            cell_texts = [cell.get_text(strip=True) for cell in cells]
                            print(f"  Row {i+1} ({len(cells)} cells): {cell_texts}")
                            
                            # 尝试解析股票代码
                            if len(cells) >= 2:
                                stock_info = cells[1].get_text(strip=True)
                                stock_match = re.search(r'(\d{6})\s*(.+)', stock_info)
                                if stock_match:
                                    stock_code = stock_match.group(1)
                                    stock_name = stock_match.group(2)
                                    print(f"    -> Parsed: {stock_code} {stock_name}")
                                    found_data = True
                                else:
                                    print(f"    -> Could not parse stock info: {stock_info}")
                        
                        if found_data:
                            print("Found valid dragon tiger data!")
                            break
                        else:
                            print("No valid data found in this table")
                    else:
                        print("No dragon tiger table found")
                        
            except Exception as e:
                print(f"Error checking date {trade_date}: {e}")
                continue

if __name__ == "__main__":
    asyncio.run(check_real_dragon_tiger_data())