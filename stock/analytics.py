#!/usr/bin/python3

from scipy import stats
import pandas as pd

# pandas data format (date, open, high, low, close, volume)

class Analytics():
    def __init__(self, data):
        self.data = data.copy()
        self.data["63ma"] = self.data["close"].rolling(window=63).mean()
        self.data["5ma"] = self.data["close"].rolling(window=5).mean()
    def pass_63ma(self):
        if self.data["5ma"].values[-1] > self.data["63ma"].values[-1] and \
           self.data["5ma"].values[-1] < self.data["63ma"].values[-1] * 1.06:
            return True
        return False

