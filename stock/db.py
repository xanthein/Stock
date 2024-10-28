import argparse
import datetime
import json
import os
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
            self.cursor.execute(f"SELECT date FROM table_{code} WHERE date = '{input_date}'")
            entry = self.cursor.fetchone()
            if entry is None:
                self.cursor.execute(f"INSERT INTO table_{code} (date, open_price, high_price, low_price, close_price, volume) VALUES ('{input_date}', {open_price}, {high_price}, {low_price}, {close_price}, {volume})")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
           description="A tool to handle data with sqlite database",
           formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    subcommand = parser.add_subparsers(dest="subcommand", help="subcommands")

    parser_trading = subcommand.add_parser("add", help="add data to db")
    parser_trading.add_argument("--trading-report", dest="trading", type=str, action="store", help="trading report file with filename trading_<yyyy-mm-dd>")

    parser.add_argument("db", type=str)

    args = parser.parse_args()
    db = DataBase(args.db)

    if args.subcommand == "add":
        try:
            if args.trading:
                date = datetime.datetime.strptime(os.path.basename(args.trading), "trading_%Y-%m-%d")
                if date.weekday() > 4:
                    print("Skip " + args.trading + ", which is Saturday/Sunday")
                else:
                    with open(args.trading, "r") as fd:
                        data = json.load(fd)
                        db.update_stock_report(date, data)
        except Exception as error:
            print(error)
