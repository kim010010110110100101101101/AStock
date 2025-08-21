import asyncio
import sys
from datetime import datetime, timedelta
sys.path.append('.')

from app.services.data_sources.tonghuashun import TongHuaShunDragonTiger, crawl_today_dragon_tiger

async def test_dragon_tiger_with_dates():
    print("Testing dragon tiger data crawling with different dates...")
    
    # 测试多个历史日期
    test_dates = [
        '2025-08-19',  # 上周一
        '2025-08-16',  # 上周五
        '2025-08-15',  # 上周四
        '2025-08-14',  # 上周三
    ]
    
    for trade_date in test_dates:
        print(f"\n=== Testing date: {trade_date} ===")
        try:
            async with TongHuaShunDragonTiger() as crawler:
                data = await crawler.fetch_dragon_tiger_data(trade_date)
                print(f"Fetched {len(data)} items for {trade_date}")
                if data:
                    print("Sample data:")
                    for i, item in enumerate(data[:2]):
                        print(f"  {i+1}. Stock: {item.get('stock_code')} {item.get('stock_name')}")
                        print(f"      Reason: {item.get('reason')}")
                        print(f"      Price: {item.get('close_price')}, Change: {item.get('change_rate')}%")
                        print(f"      Turnover: {item.get('turnover')}, Net Buy: {item.get('net_buy_amount')}")
                    # 如果找到数据就停止测试
                    break
                else:
                    print("No data returned")
        except Exception as e:
            print(f"Test failed for {trade_date}: {e}")

if __name__ == "__main__":
    asyncio.run(test_dragon_tiger_with_dates())