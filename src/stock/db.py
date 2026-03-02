#!/usr/bin/env python3
import sqlite3

class DataBase:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.cursor = self.conn.cursor()
    def __del__(self):
        self.conn.commit()
        self.conn.close()
    def update_stock_report(self, date, data):
        for stock in data:
            code = stock["Code"]
            input_date = date.strftime("%Y-%m-%d")
            open_price = float(stock["OpeningPrice"]) if stock["OpeningPrice"] else 0.0
            high_price = float(stock["HighestPrice"]) if stock["HighestPrice"] else 0.0
            low_price = float(stock["LowestPrice"]) if stock["LowestPrice"] else 0.0
            close_price = float(stock["ClosingPrice"]) if stock["ClosingPrice"] else 0.0
            volume = int(stock["TradeVolume"]) if stock["TradeVolume"] else 0
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS table_{code} (date STRING, open_price REAL, high_price REAL, low_price REAL, close_price REAL, volume INTEGER)")
            self.cursor.execute(f"SELECT * FROM table_{code} WHERE open_price = '{open_price}' AND high_price = '{high_price}' AND low_price = '{low_price}' AND close_price = '{close_price}'")
            entry = self.cursor.fetchone()
            if entry is None:
                self.cursor.execute(f"INSERT INTO table_{code} (date, open_price, high_price, low_price, close_price, volume) VALUES ('{input_date}', {open_price}, {high_price}, {low_price}, {close_price}, {volume})")
    def get_stock_report(self, code, count):
            self.cursor.execute(f"SELECT * FROM (SELECT * FROM table_{code} ORDER BY date DESC LIMIT {count}) AS last_row ORDER BY date ASC")
            return self.cursor.fetchall()
