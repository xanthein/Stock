#!/usr/bin/python3

import datetime
import time
from scipy import stats
import numpy
import twstock
import csv

def pass_63ma(stock):
    stock = twstock.Stock(stock, False)
    today = datetime.datetime.today()
    before = today - datetime.timedelta(days=100)
    stock.fetch_from(before.year, before.month)
    price = list(filter(lambda x: x!=None, stock.price))
    if len(price) < 63 or stock.price[-1] == None:
        return False
    try:
        ma = stock.moving_average(price, 63)
        slope, intercept, rvalue, pvalue, stderr = stats.linregress(ma, numpy.arange(0, len(ma)))
        if stock.price[-1] > ma[-1] and \
            stock.price[-1] < ma[-1] * 1.06 and \
            slope > 0:
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False

with open('stock.csv', 'r') as csvfile:
    rows = csv.reader(csvfile)
    for row in rows:
        print('%s %s' % (row[0], row[1]))
        if pass_63ma(row[0]):
            print("%s" % row[0])
