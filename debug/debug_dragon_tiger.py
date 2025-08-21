import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import sys
sys.path.append('.')

async def debug_table_structure():
    """调试表格结构和数据格式"""
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
    
    # 测试前几天的日期
    test_dates = [
        (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),  # 昨天
        (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),  # 前天
        (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),  # 大前天
    ]
    
    async with aiohttp.ClientSession(headers=headers) as session:
        for trade_date in test_dates:
            print(f"\n=== Analyzing date: {trade_date} ===")
            
            try:
                url = f"{dragon_tiger_url}?date={trade_date.replace('-', '')}"
                print(f"Request URL: {url}")
                
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"HTTP request failed: {response.status}")
                        continue
                    
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # 查找龙虎榜相关的表格
                    tables = soup.find_all('table')
                    print(f"Total tables found: {len(tables)}")
                    
                    # 查找可能包含龙虎榜数据的表格
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
                        for i, table in enumerate(tables):
                            headers = table.find_all('th')
                            if headers and len(headers) >= 6:
                                header_text = ' '.join([th.get_text(strip=True) for th in headers])
                                print(f"Table {i+1} headers: {header_text}")
                                if any(keyword in header_text for keyword in ['代码', '名称', '涨跌幅', '成交额', '净买入']):
                                    print(f"Found dragon tiger table by headers: Table {i+1}")
                                    dragon_tiger_table = table
                                    break
                    
                    if dragon_tiger_table:
                        print("\n=== Analyzing dragon tiger table structure ===")
                        
                        # 分析表格结构
                        thead = dragon_tiger_table.find('thead')
                        tbody = dragon_tiger_table.find('tbody')
                        
                        print(f"Has thead: {thead is not None}")
                        print(f"Has tbody: {tbody is not None}")
                        
                        # 分析表头
                        if thead:
                            header_rows = thead.find_all('tr')
                            print(f"Header rows: {len(header_rows)}")
                            for i, row in enumerate(header_rows):
                                headers = row.find_all(['th', 'td'])
                                header_texts = [h.get_text(strip=True) for h in headers]
                                print(f"  Header row {i+1}: {header_texts}")
                        else:
                            # 如果没有thead，查看第一行是否是表头
                            first_row = dragon_tiger_table.find('tr')
                            if first_row:
                                headers = first_row.find_all(['th', 'td'])
                                header_texts = [h.get_text(strip=True) for h in headers]
                                print(f"  First row (potential headers): {header_texts}")
                        
                        # 分析数据行
                        if tbody:
                            data_rows = tbody.find_all('tr')
                        else:
                            all_rows = dragon_tiger_table.find_all('tr')
                            data_rows = all_rows[1:] if len(all_rows) > 1 else all_rows  # 跳过表头行
                        
                        print(f"Data rows: {len(data_rows)}")
                        
                        # 分析前几行数据
                        for i, row in enumerate(data_rows[:3]):
                            cells = row.find_all(['td', 'th'])
                            cell_texts = [cell.get_text(strip=True) for cell in cells]
                            print(f"  Data row {i+1} ({len(cells)} cells): {cell_texts}")
                        
                        # 如果找到数据就停止测试其他日期
                        if len(data_rows) > 0:
                            print("Found data, stopping date testing")
                            break
                    else:
                        print("No dragon tiger table found")
                        
            except Exception as e:
                print(f"Error analyzing date {trade_date}: {e}")
                continue

if __name__ == "__main__":
    asyncio.run(debug_table_structure())