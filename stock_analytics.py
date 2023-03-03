#!/usr/bin/python3

import sys
import datetime
import time
from scipy import stats
import numpy
import twstock
import csv

class Analytics(object):

    def pass_63ma(stock):
        stock = twstock.Stock(stock, False)
        today = datetime.datetime.today()
        before = today - datetime.timedelta(days=90)
        stock.fetch_from(before.year, before.month)
        price = list(filter(lambda x: x!=None, stock.price))
        if len(price) < 63 or stock.price[-1] == None:
            return False, []
        try:
            ma63 = stock.moving_average(price, 63)
            ma5 = stock.moving_average(price, 5)
            ma5_slope, intercept, rvalue, pvalue, stderr = stats.linregress(ma5, numpy.arange(0, len(ma5)))
            if ma5[-1] > ma63[-1] and \
                ma5[-1] < ma63[-1] * 1.06 and \
                ma5_slope > 0:
                return True, stock
            else:
                return False, []
        except Exception as e:
            print(e)
            return False, []
