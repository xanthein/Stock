#!/usr/bin/python

from grs import Stock
from grs import TWSENo

twse_no = TWSENo()

for stock_no in twse_no.get_stock_list():
    try:
        stock_120 = Stock(stock_no, 120)
        price_120 = stock_120.price
        m120 = sum(price_120) / len(price_120)

        stock_1 = Stock(stock_no, 1)
        price_1 = stock_1.price
        m1 = sum(price_1) / len(price_1)

        if m1 > m120:
            print stock_1.info[1] + ' Pass 10 years line'

    except:
        pass
