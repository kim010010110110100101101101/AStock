# -*- coding: utf-8 -*-
import asyncio
import sys
import os
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.data_sources.tonghuashun import TongHuaShunDragonTiger
from app.models.dragon_tiger import DragonTiger
from app.core.database import get_db
from sqlalchemy.orm import Session

async def test_database_insert():
    """测试龙虎榜数据入库"""
    print("Testing dragon tiger data insertion to database...")
    
    # 获取龙虎榜数据
    async with TongHuaShunDragonTiger() as crawler:
        try:
            data = await crawler.fetch_dragon_tiger_data('2024-12-20')
            print(f"Fetched {len(data)} records from TongHuaShun")
            
            if not data:
                print("No data to insert")
                return
            
            # 获取数据库会话
            db_gen = get_db()
            db: Session = next(db_gen)
            
            try:
                # 插入前3条数据作为测试
                inserted_count = 0
                for item in data[:3]:
                    # 转换日期格式 YYYY-MM-DD -> YYYYMMDD
                    trade_date_str = item['trade_date'].replace('-', '')
                    
                    # 检查是否已存在
                    existing = db.query(DragonTiger).filter(
                        DragonTiger.ts_code == item['stock_code'],
                        DragonTiger.trade_date == trade_date_str
                    ).first()
                    
                    if existing:
                        print(f"Record already exists: {item['stock_code']} {item['stock_name']}")
                        continue
                    
                    # 创建新记录
                    dragon_tiger_record = DragonTiger(
                        ts_code=item['stock_code'],
                        stock_name=item['stock_name'],
                        trade_date=trade_date_str,
                        reason=item['reason'],
                        close_price=item['close_price'],
                        pct_change=item['change_rate'],
                        amount=item['turnover'],
                        net_amount=item['net_buy_amount'],
                        data_source=item['data_source']
                    )
                    
                    db.add(dragon_tiger_record)
                    inserted_count += 1
                    print(f"Prepared to insert: {item['stock_code']} {item['stock_name']}")
                
                # 提交事务
                db.commit()
                print(f"Successfully inserted {inserted_count} records to database")
                
                # 验证插入结果
                total_records = db.query(DragonTiger).count()
                print(f"Total records in database: {total_records}")
                
                # 显示最新的几条记录
                latest_records = db.query(DragonTiger).order_by(DragonTiger.created_at.desc()).limit(3).all()
                print("\nLatest 3 records in database:")
                for record in latest_records:
                    print(f"  {record.ts_code} {record.stock_name} - {record.trade_date} - Source: {record.data_source}")
                    
            except Exception as db_error:
                db.rollback()
                print(f"Database error: {db_error}")
            finally:
                db.close()
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_database_insert())