import pymysql
from sqlalchemy import create_engine
from app.core.config import settings
from app.core.database import Base
from app.models import dragon_tiger, stock, stock_basic, stock_daily

def create_database():
    try:
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='111111',
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS astock CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("Database 'astock' created successfully")
        
        connection.commit()
        connection.close()
        
    except Exception as e:
        print("Failed to create database:", str(e))
        raise

def create_tables():
    try:
        engine = create_engine(settings.DATABASE_URL, echo=True)
        Base.metadata.create_all(bind=engine)
        print("Data tables created successfully")
        
    except Exception as e:
        print("Failed to create tables:", str(e))
        raise

def main():
    print("Starting to create MySQL database and table structure...")
    create_database()
    create_tables()
    print("MySQL database and table structure creation completed!")

if __name__ == "__main__":
    main()