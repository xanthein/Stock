#!/usr/bin/python3

import csv
import time
import MySQLdb as sql
from io import StringIO
from save_bsr_csv import get_bsr_csv
from save_bsr_csv import get_bsr_date

def update_stock_bsr(stock):
    date = time.strftime('%Y-%m-%d', time.localtime())

    if get_bsr_date() != date:
        print("date wrong")
        return

    csvfile = StringIO(get_bsr_csv(stock))

    conn = sql.connect(user='dirk@localhost', passwd='pass', db='bsr', charset="utf8")
    cur = conn.cursor()
    try:
        cur.execute('''SELECT date FROM `%s` LIMIT 1;''' % stock)
        conn.commit()
    except (sql.Error) as e:
        cur.execute('''CREATE TABLE IF NOT EXISTS `%s` ( date DATE NOT NULL, broker VARCHAR(20) NOT NULL, price FLOAT NOT NULL, buy INT NOT NULL, sell INT NOT NULL );''' % stock)
        conn.commit()

    cur.execute('''SELECT * FROM `%s` WHERE date = "%s";''' % (stock, date))
    if len(cur.fetchall()) == 0:
        rows = csv.reader(csvfile)
        next(rows)
        next(rows)
        next(rows)
        for row in rows:
            if len(row) == 0:
                continue
            if row[1] != '':
                cur.execute('''INSERT INTO `%s` (date, broker, price, buy, sell) VALUES ("%s", "%s", %f, %d, %d);''' %
                        (stock, date, row[1][4:], float(row[2]), int(row[3]), int(row[4])))
                conn.commit()
            if row[7] != '':
                cur.execute('''INSERT INTO `%s`(date, broker, price, buy, sell) VALUES ("%s", "%s", %f, %d, %d);''' %
                        (stock, date, row[7][4:], float(row[8]), int(row[9]), int(row[10])))
                conn.commit()
