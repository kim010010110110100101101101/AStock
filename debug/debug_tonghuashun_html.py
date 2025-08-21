# -*- coding: utf-8 -*-
import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def debug_tonghuashun_html():
    """调试同花顺龙虎榜页面的HTML结构"""
    url = "http://data.10jqka.com.cn/market/longhu/2024-12-20/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=30) as response:
                if response.status != 200:
                    print(f"HTTP Status: {response.status}")
                    return
                
                html_content = await response.text()
                print(f"HTML Content Length: {len(html_content)}")
                
                # 保存HTML到文件以便查看
                with open('tonghuashun_debug.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print("HTML saved to tonghuashun_debug.html")
                
                # 解析HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 查找所有表格
                tables = soup.find_all('table')
                print(f"Found {len(tables)} tables")
                
                for i, table in enumerate(tables):
                    print(f"\nTable {i+1}:")
                    print(f"  Classes: {table.get('class', [])}")
                    print(f"  ID: {table.get('id', 'None')}")
                    
                    # 查看表头
                    headers = table.find_all('th')
                    if headers:
                        header_texts = [th.get_text(strip=True) for th in headers]
                        print(f"  Headers: {header_texts}")
                    
                    # 查看第一行数据
                    rows = table.find_all('tr')
                    if len(rows) > 1:  # 跳过表头行
                        first_data_row = rows[1] if len(rows) > 1 else rows[0]
                        cells = first_data_row.find_all(['td', 'th'])
                        if cells:
                            cell_texts = [cell.get_text(strip=True) for cell in cells[:8]]  # 只显示前8列
                            print(f"  First row data: {cell_texts}")
                
                # 查找包含龙虎榜关键词的div或其他元素
                print("\nSearching for dragon tiger related content...")
                dragon_elements = soup.find_all(text=lambda text: text and ('龙虎榜' in text or '涨跌幅' in text or '成交额' in text))
                for elem in dragon_elements[:5]:  # 只显示前5个
                    print(f"  Found text: {elem.strip()[:100]}...")
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_tonghuashun_html())