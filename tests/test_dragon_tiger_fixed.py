#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的龙虎榜数据爬取功能（包含AKShare备用数据源）
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.data_sources.tonghuashun import TongHuaShunDragonTiger
from app.services.data_sources.akshare_source import AkshareDataSource
from app.core.logging import get_logger

logger = get_logger('test')

async def test_akshare_direct():
    """直接测试AKShare龙虎榜数据获取"""
    print("\n=== 直接测试AKShare龙虎榜数据获取 ===")
    
    try:
        akshare_source = AkshareDataSource()
        
        # 测试多个历史日期
        test_dates = ['20241220', '20241219', '20241218', '20241217', '20241216']
        
        for test_date in test_dates:
            print(f"\n--- 测试日期: {test_date} ---")
            try:
                data = await akshare_source.fetch_dragon_tiger_data(test_date)
                print(f"获取到数据: {len(data)} 条")
                
                if data:
                    print("数据样本:")
                    for i, item in enumerate(data[:3]):  # 显示前3条
                        print(f"  {i+1}. {item['ts_code']} {item['name']}")
                        print(f"     涨跌幅: {item['pct_chg']}%, 成交额: {item['turnover']}, 净买入: {item['net_amount']}")
                    break  # 找到数据后停止测试其他日期
                else:
                    print("未获取到数据")
                    
            except Exception as e:
                print(f"日期 {test_date} 测试失败: {e}")
                
    except Exception as e:
        print(f"AKShare初始化失败: {e}")

async def test_tonghuashun_with_fallback():
    """测试同花顺龙虎榜数据爬取（包含AKShare备用数据源）"""
    print("\n=== 测试同花顺龙虎榜数据爬取（包含AKShare备用数据源） ===")
    
    # 测试多个历史日期
    test_dates = [
        '2024-12-20',
        '2024-12-19', 
        '2024-12-18',
        '2024-12-17',
        '2024-12-16'
    ]
    
    async with TongHuaShunDragonTiger() as crawler:
        for test_date in test_dates:
            print(f"\n--- 测试日期: {test_date} ---")
            try:
                data = await crawler.fetch_dragon_tiger_data(test_date)
                print(f"获取到数据: {len(data)} 条")
                
                if data:
                    print("数据样本:")
                    for i, item in enumerate(data[:3]):  # 显示前3条
                        print(f"  {i+1}. {item['stock_code']} {item['stock_name']} - 数据源: {item.get('data_source', 'unknown')}")
                        print(f"     涨跌幅: {item['change_rate']}%, 成交额: {item['turnover']}, 净买入: {item['net_buy_amount']}")
                    break  # 找到数据后停止测试其他日期
                else:
                    print("未获取到数据")
                    
            except Exception as e:
                print(f"测试失败: {e}")

async def main():
    """主测试函数"""
    print("开始测试修复后的龙虎榜数据爬取功能...")
    
    # 测试1: 直接测试AKShare
    await test_akshare_direct()
    
    # 测试2: 测试同花顺（包含AKShare备用数据源）
    await test_tonghuashun_with_fallback()
    
    print("\n测试完成！")

if __name__ == "__main__":
    asyncio.run(main())