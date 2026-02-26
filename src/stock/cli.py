#!/usr/bin/env python3

import argparse
import csv
import datetime
import json
import os
import pandas as pd
import sys
from stock.analytics import Analytics
from stock.db import DataBase
from stock.fetcher import TWSEDataFetcher
from stock.draw import Draw


def do_analyse(stock_symbol_path, database_path, verbose):
    with open(stock_symbol_path, "r") as csvfile:
        db = DataBase(database_path)
        rows = csv.reader(csvfile)
        for row in rows:
            if verbose:
                print("%s %s" % (row[0], row[1]))
            data = db.get_stock_report(row[0], 90)
            df = pd.DataFrame(
                data, columns=["date", "open", "high", "low", "close", "volume"]
            )
            df.set_index("date", inplace=True)
            df.index = pd.to_datetime(df.index)
            analytic = Analytics(df)
            if analytic.pass_63ma():
                Draw.DrawCandle(row[0], df)


def run():
    parser = argparse.ArgumentParser()
    subcmd = parser.add_subparsers(dest="subcmd", help="subcommand")
    cmd_analyse = subcmd.add_parser("analyse")
    cmd_analyse.add_argument("--stock", help="stock number to handle with", type=int)
    cmd_analyse.add_argument("--csv", help="csv file with stock number to handle with")
    cmd_analyse.add_argument("--db", help="database file with stock trading datas", type=str)
    cmd_db = subcmd.add_parser("database")
    cmd_db_subcmd = cmd_db.add_subparsers(dest="db_subcmd", help="db subcommand")
    cmd_db_action = cmd_db_subcmd.add_parser("add", help="add data to db")
    cmd_db_action.add_argument("--trading-report", dest="trading", type=str, action="store", help="trading report file with filename trading_<yyyy-mm-dd>")
    cmd_db.add_argument("--db", help="database file with stock trading datas", type=str)
    cmd_fetcher = subcmd.add_parser("fetcher")
    cmd_fetcher_subcmd = cmd_fetcher.add_subparsers(dest="report_subcmd", help="report subcommand")
    cmd_fetcher_financial = cmd_fetcher_subcmd.add_parser("financial", help="Get financial report")
    cmd_fetcher_financial.add_argument("--year", dest="year", type=int, action="store", required=True, help="Which year to get report")
    cmd_fetcher_financial.add_argument("stock", type=int)
    cmd_fetcher_trading = cmd_fetcher_subcmd.add_parser("trading", help="Get TWSE day trading report")
    parser.add_argument("--verbose", action="store_true")

    args = parser.parse_args()
    if args.subcmd == "analyse":
        do_analyse(args.csv, args.db, args.verbose)
    elif args.subcmd == "database":
        db = DataBase(args.db)
        if args.db_subcmd == "add":
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
    elif args.subcmd == "fetcher":
        if args.report_subcmd == "trading":
            fetcher = TWSEDataFetcher()
            date, data = fetcher.get_stock_day_trading_report()
            with open("trading_" + date.strftime("%Y-%m-%d"), "w") as fd:
                json.dump(data, fd)
