#!/usr/bin/python3

import argparse
import threading
import csv
import time
import twstock
from stock.analytics import Analytics
from stock.draw import Draw
from stock.db_bsr import update_stock_bsr

def do_save_bsr(filename, verb):
    with open(filename, 'r') as csvfile:
        rows = csv.reader(csvfile)
        for row in rows:
            if(verb):
                print('%s %s' % (row[0], row[1]))
            t1 = threading.Thread(target = update_stock_bsr, args = (row[0],))
            t1.start()
            time.sleep(2.0)
            next_row = next(rows)
            if(verb):
                print('%s %s' % (next_row[0], next_row[1]))
            t2 = threading.Thread(target = update_stock_bsr, args = (next_row[0],))
            t2.start()
            t1.join()
            t2.join()

def do_analyse(filename, verb):
    with open(filename, 'r') as csvfile:
        rows = csv.reader(csvfile)
        for row in rows:
            if(verb):
                print('%s %s' % (row[0], row[1]))
            ret,stock = Analytics.pass_63ma(row[0])
            if ret:
                Draw.DrawCandle(stock)
            time.sleep(25)

def run(argv):
    parser = argparse.ArgumentParser()
    command = parser.add_mutually_exclusive_group()
    command.add_argument('--save_bsr', help='Save the buy-sell report for stock',
            action='store_true')
    command.add_argument('--analyse', help='Analyse stock',
            action='store_true')
    stock_arg = parser.add_mutually_exclusive_group()
    stock_arg.add_argument('--stock', help='stock number to handle with', type=int)
    stock_arg.add_argument('--csv', help='csv file with stock number to handle with')
    parser.add_argument('--verbose', action='store_true')

    args = parser.parse_args()
    if(args.save_bsr):
        if(args.csv):
            do_save_bsr(args.csv, args.verbose)
        elif(args.stock):
            print(args.stock)
        else:
            parser.print_help()
    elif(args.analyse):
        if(args.csv):
            do_analyse(args.csv, args.verbose)
        elif(args.stock):
            print(args.stock)
        else:
            parser.print_help()
    else:
        parser.print_help()
