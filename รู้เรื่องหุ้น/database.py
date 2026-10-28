import sqlite3
from pathlib import Path


# ตำแหน่งของไฟล์ stock.db
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "stock.db"


def connect_database():
    """
    เชื่อมต่อกับฐานข้อมูล
    """

    connection = sqlite3.connect(DATABASE_PATH)

    # เปิดการตรวจสอบ Foreign Key
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def init_database():
    """
    สร้างตารางที่ใช้ในโปรเจกต์
    """

    connection = connect_database()
    cursor = connection.cursor()

    try:

        # ตารางเก็บข้อมูลหุ้น
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL UNIQUE,
                name TEXT,
                exchange TEXT
            )
        """)

        # ตรวจสอบว่ามี column อะไรอยู่แล้ว
        cursor.execute("PRAGMA table_info(stocks)")

        rows = cursor.fetchall()

        stock_columns = set()

        for row in rows:
            stock_columns.add(row[1])

        # เพิ่ม column ที่ยังไม่มี
        extra_columns = {
            "industry": "TEXT",
            "country": "TEXT",
            "market_cap": "REAL",
            "website": "TEXT",
            "updated_at": "TEXT"
        }

        for column_name in extra_columns:

            if column_name not in stock_columns:

                column_type = extra_columns[column_name]

                sql = (
                    "ALTER TABLE stocks ADD COLUMN "
                    + column_name
                    + " "
                    + column_type
                )

                cursor.execute(sql)

        # ตารางเก็บหุ้นใน Portfolio
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL UNIQUE,
                company TEXT,
                amount REAL NOT NULL,
                industry TEXT
            )
        """)

        connection.commit()

    except Exception as error:

        connection.rollback()

        print("เกิดข้อผิดพลาดในการสร้างฐานข้อมูล:", error)

        raise

    finally:

        connection.close()


def get_stock(symbol):
    """
    ค้นหาข้อมูลหุ้นจากฐานข้อมูล
    """

    connection = connect_database()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                symbol,
                name,
                exchange,
                industry,
                country,
                market_cap,
                website,
                updated_at
            FROM stocks
            WHERE symbol = ?
        """, (symbol.upper(),))

        result = cursor.fetchone()

        return result

    finally:

        connection.close()


def upsert_stock(stock):
    """
    เพิ่มหรือแก้ไขข้อมูลหุ้นในฐานข้อมูล
    """

    connection = connect_database()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO stocks (
                symbol,
                name,
                exchange,
                industry,
                country,
                market_cap,
                website,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(symbol) DO UPDATE SET
                name = excluded.name,
                exchange = excluded.exchange,
                industry = excluded.industry,
                country = excluded.country,
                market_cap = excluded.market_cap,
                website = excluded.website,
                updated_at = excluded.updated_at
        """, (
            stock.get("symbol"),
            stock.get("company_name"),
            stock.get("exchange"),
            stock.get("industry"),
            stock.get("country"),
            stock.get("market_cap"),
            stock.get("website"),
            stock.get("updated_at")
        ))

        connection.commit()

    except Exception as error:

        connection.rollback()

        print("ไม่สามารถบันทึกข้อมูลหุ้น:", error)

        raise

    finally:

        connection.close()


def save_portfolio_holding(stock):
    """
    เพิ่มหุ้นลงใน Portfolio
    """

    connection = connect_database()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO portfolio_holdings (
                symbol,
                company,
                amount,
                industry
            )
            VALUES (?, ?, ?, ?)
        """, (
            stock["symbol"],
            stock["company"],
            stock["amount"],
            stock["industry"]
        ))

        connection.commit()

        return True

    except Exception as error:

        connection.rollback()

        print("ไม่สามารถเพิ่มหุ้นใน Portfolio:", error)

        raise

    finally:

        connection.close()


def get_portfolio_holdings():
    """
    ดึงหุ้นทั้งหมดที่อยู่ใน Portfolio
    """

    connection = connect_database()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                symbol,
                company,
                amount,
                industry
            FROM portfolio_holdings
            ORDER BY id
        """)

        result = cursor.fetchall()

        return result

    finally:

        connection.close()


def update_portfolio_amount(symbol, amount):
    """
    แก้ไขจำนวนเงินของหุ้นใน Portfolio
    """

    connection = connect_database()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            UPDATE portfolio_holdings
            SET amount = ?
            WHERE symbol = ?
        """, (
            amount,
            symbol.upper()
        ))

        connection.commit()

    except Exception as error:

        connection.rollback()

        print("ไม่สามารถแก้ไขจำนวนเงิน:", error)

        raise

    finally:

        connection.close()


def delete_portfolio_holding(symbol):
    """
    ลบหุ้นออกจาก Portfolio
    """

    connection = connect_database()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            DELETE FROM portfolio_holdings
            WHERE symbol = ?
        """, (symbol.upper(),))

        connection.commit()

    except Exception as error:

        connection.rollback()

        print("ไม่สามารถลบหุ้น:", error)

        raise

    finally:

        connection.close()


def clear_portfolio_holdings():
    """
    ลบหุ้นทั้งหมดออกจาก Portfolio
    """

    connection = connect_database()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            DELETE FROM portfolio_holdings
        """)

        connection.commit()

    except Exception as error:

        connection.rollback()

        print("ไม่สามารถล้าง Portfolio:", error)

        raise

    finally:

        connection.close()


if __name__ == "__main__":

    init_database()

    print(
        "Database พร้อมใช้งาน:",
        DATABASE_PATH
    )