#!/usr/bin/env python3

import csv
import pymysql as sql
from io import StringIO
from stock.save_bsr_csv import get_bsr_csv
from stock.save_bsr_csv import get_bsr_date

def update_stock_bsr(stock):

    date = get_bsr_date()

    conn = sql.connect(host='localhost',
                       user='dirk',
                       passwd='pass',
                       db='bsr',
                       charset='utf8',
                       cursorclass=sql.cursors.DictCursor)
    cur = conn.cursor()
    try:
        cur.execute('''SELECT date FROM `{stock}` LIMIT 1;'''.format(stock=stock))
        conn.commit()
    except (sql.Error) as e:
        cur.execute('''CREATE TABLE IF NOT EXISTS `{stock}` ( date DATE NOT NULL, broker VARCHAR(20) NOT NULL, price FLOAT NOT NULL, buy INT NOT NULL, sell INT NOT NULL );'''.format(stock=stock))
        conn.commit()

    cur.execute('''SELECT * FROM `{stock}` WHERE date = "{date}";'''.format(stock=stock, date=date))

    #make sure nothing duplicated
    if len(cur.fetchall()) == 0:
        data = get_bsr_csv(stock)
        if data == 'None':
            return
        csvfile = StringIO(data)
        rows = csv.reader(csvfile)
        try:
            next(rows)
            next(rows)
            next(rows)

            for row in rows:
                if len(row) == 0:
                    continue
                if row[1] != '':
                    cur.execute('''INSERT INTO `{stock}` (date, broker, price, buy, sell) VALUES ("{date}", "{broker}", {price:f}, {buy:d}, {sell:d});'''.format(stock=stock, date=date, broker=row[1][4:], price=float(row[2]), buy=int(row[3]), sell=int(row[4])))
                    conn.commit()
                if row[7] != '':
                    cur.execute('''INSERT INTO `{stock}` (date, broker, price, buy, sell) VALUES ("{date}", "{broker}", {price:f}, {buy:d}, {sell:d});'''.format(stock=stock, date=date, broker=row[7][4:], price=float(row[8]), buy=int(row[9]), sell=int(row[10])))
                    conn.commit()
        except:
            print('Something wrong with bsr csv data')
    else:
        print('find duplicated date {date} in {stock}'.format(date=date, stock=stock))
