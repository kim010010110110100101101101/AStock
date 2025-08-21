# -*- coding: utf-8 -*-
import asyncio
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.data_sources.tonghuashun import TongHuaShunDragonTiger

async def test_tonghuashun():
    print("Testing TongHuaShun dragon tiger data...")
    
    # Test dates
    test_dates = ['2024-12-20', '2024-12-19', '2024-12-18']
    
    async with TongHuaShunDragonTiger() as crawler:
        for test_date in test_dates:
            print(f"\nTesting date: {test_date}")
            try:
                data = await crawler.fetch_dragon_tiger_data(test_date)
                print(f"Got {len(data)} records")
                
                if data:
                    print("First 3 records:")
                    for i, item in enumerate(data[:3]):
                        print(f"  {i+1}. {item['stock_code']} {item['stock_name']} - Source: {item.get('data_source', 'unknown')}")
                        print(f"     Change: {item['change_rate']}%, Turnover: {item['turnover']}, Net: {item['net_buy_amount']}")
                    break
                else:
                    print("No data found")
                    
            except Exception as e:
                print(f"Date {test_date} failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_tonghuashun())