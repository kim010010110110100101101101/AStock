# -*- coding: utf-8 -*-
import asyncio
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.data_sources.akshare_source import AkshareDataSource

async def test_akshare():
    print("Testing AKShare dragon tiger data...")
    
    try:
        akshare_source = AkshareDataSource()
        
        # Test dates
        test_dates = ['20241220', '20241219', '20241218']
        
        for test_date in test_dates:
            print(f"\nTesting date: {test_date}")
            try:
                data = await akshare_source.fetch_dragon_tiger_data(test_date)
                print(f"Got {len(data)} records")
                
                if data:
                    print("First 3 records:")
                    for i, item in enumerate(data[:3]):
                        print(f"  {i+1}. {item['ts_code']} {item['name']}")
                        print(f"     Change: {item['pct_chg']}%, Net amount: {item['net_amount']}")
                    break
                else:
                    print("No data found")
                    
            except Exception as e:
                print(f"Date {test_date} failed: {e}")
                
    except Exception as e:
        print(f"AKShare init failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_akshare())