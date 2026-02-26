#!/usr/bin/env python3
import mplfinance as mpf
import pandas as pd


class Draw(object):

    # pandas data format (open, high, low, close, volume) with date as index
    def DrawCandle(stock_symbol, data):
        mc = mpf.make_marketcolors(up="r", down="g", inherit=True)
        s = mpf.make_mpf_style(base_mpf_style="yahoo", marketcolors=mc)
        kwargs = dict(
            type="candle",
            mav=(5, 20, 60),
            volume=True,
            title=stock_symbol,
            style=s,
            savefig=stock_symbol + ".png",
        )
        mpf.plot(data, **kwargs)
