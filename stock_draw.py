#!/usr/bin/python3
import mplfinance as mpf
import pandas as pd

class Draw(object):

    def DrawCandle(data):
        df = pd.DataFrame(list(zip(data.open, data.high, data.low, data.close, data.capacity)), columns=['Open', 'High', 'Low', 'Close', 'Volume'], index=data.date)
        mc = mpf.make_marketcolors(up='r', down='g', inherit=True)
        s  = mpf.make_mpf_style(base_mpf_style='yahoo', marketcolors=mc)
        kwargs = dict(type='candle', mav=(5,20,60), volume=True, title=data.sid, style=s, savefig=data.sid+'.png')
        mpf.plot(df, **kwargs)
