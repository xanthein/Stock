#!/usr/bin/env python3

from scipy import stats
import pandas as pd
import numpy

# pandas data format (open, high, low, close, volume) with date as index

class Analytics():
    def __init__(self, data):
        self.data = data.copy()
        self.data["63ma"] = self.data["close"].rolling(window=63).mean()
        self.data["5ma"] = self.data["close"].rolling(window=5).mean()
    def pass_63ma(self):
        ma5_drop = self.data["5ma"].dropna()
        ma5_cal = stats.linregress(numpy.arange(0, len(ma5_drop)), ma5_drop)
        if self.data["5ma"].values[-1] > self.data["63ma"].values[-1] and \
           ma5_cal.slope > 0:
            for i in self.data["5ma"].values[-5:]:
                if i < self.data["63ma"].values[-1]:
                    return True
        return False

