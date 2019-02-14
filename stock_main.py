#!/usr/bin/python3

import threading
import csv
import time
from db_bsr import update_stock_bsr

if __name__ == '__main__':
    with open('stock.csv', 'r') as csvfile:
        rows = csv.reader(csvfile)
        for row in rows:
            print('%s %s' % (row[0], row[1]))
            t1 = threading.Thread(target = update_stock_bsr, args = (row[0],))
            t1.start()
            time.sleep(2.0)
            next_row = next(rows)
            print('%s %s' % (next_row[0], next_row[1]))
            t2 = threading.Thread(target = update_stock_bsr, args = (next_row[0],))
            t2.start()
            t1.join()
            t2.join()
