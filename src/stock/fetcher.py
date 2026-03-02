#!/usr/bin/env python3
import sys
import requests
import pandas as pd
import twstock
import time
import datetime
import json
from bs4 import BeautifulSoup

class FinancialReportFetcher:
    """Fetches financial reports for individual stocks from MOPS."""

    BASE_URLS = {
        'BalanceSheet':      'https://mops.twse.com.tw/mops/web/ajax_t164sb03',
        'ProfitAndLose':     'https://mops.twse.com.tw/mops/web/ajax_t164sb04',
        'CashFlowStatement': 'https://mops.twse.com.tw/mops/web/ajax_t164sb05',
        'Dividend':          'https://mops.twse.com.tw/mops/web/ajax_t05st09',
        'Revenu':            'https://mops.twse.com.tw/mops/web/ajax_t05st10_ifrs',
        'HoldingShare':      'https://mops.twse.com.tw/mops/web/ajax_stapap1',
    }

    def __init__(self, stock_number):
        self.stock_number = stock_number

    @staticmethod
    def _to_roc_year(year):
        return year - 1911 if year >= 1000 else year

    def fetch(self, year, season, report_type='BalanceSheet'):
        url = self.BASE_URLS[report_type]
        year = self._to_roc_year(year)

        form_data = {
            'encodeURIComponent': 1,
            'step': 1,
            'firstin': 1,
            'off': 1,
            'TYPEK': 'all',
            'co_id': self.stock_number,
            'isnew': 'false',
            'year': year,
            'season': season,
        }

        if report_type in ('HoldingShare', 'Revenu'):
            form_data.pop('season', None)
            form_data['month'] = "%02d" % season

        r = requests.post(url, form_data)
        soup = BeautifulSoup(r.text, 'html.parser')
        if soup.select('input[type=button]') is not None:
            form_data['step'] = 2
            r = requests.post(url, form_data)

        idx = 4 if report_type == 'HoldingShare' else 1
        return pd.read_html(r.text)[idx].fillna("")


class MarketDataFetcher:
    """Fetches aggregated market-wide financial data from MOPS."""

    @staticmethod
    def _to_roc_year(year):
        return year - 1911 if year > 1911 else year

    @staticmethod
    def _fetch_from_url(url, year, season):
        form_data = {
            'encodeURIComponent': 1,
            'step': 1,
            'firstin': 1,
            'off': 1,
            'isQuery': 'Y',
            'TYPEK': 'sii',
            'year': year,
            'season': season,
        }
        r = requests.post(url, form_data)
        return pd.read_html(r.text)

    def get_revenue(self, year, month):
        year = self._to_roc_year(year)
        suffix = f'{year}_{month}' if year <= 98 else f'{year}_{month}_0'
        url = f'https://mops.twse.com.tw/nas/t21/sii/t21sc03_{suffix}.html'

        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        r = requests.get(url, headers=headers)
        r.encoding = 'big5'

        dfs = pd.read_html(r.text, encoding='big-5')
        df = pd.concat([df for df in dfs if 5 < df.shape[1] <= 11])

        if 'levels' in dir(df.columns):
            df.columns = df.columns.get_level_values(1)
        else:
            df = df[list(range(0, 10))]
            column_index = df.index[(df[0] == '公司代號')][0]
            df.columns = df.iloc[column_index]

        df['當月營收'] = pd.to_numeric(df['當月營收'], 'coerce')
        df = df[~df['當月營收'].isnull()]
        df = df[df['公司代號'] != '合計']
        return df

    def get_balance_sheet(self, year, season):
        year = self._to_roc_year(year)
        url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb05'
        dfs = self._fetch_from_url(url, year, season)
        return pd.concat(
            df.rename(columns={
                '資產總額': '資產總計', '負債總額': '負債總計', '權益總額': '權益總計'
            })[['公司代號', '公司名稱', '資產總計', '負債總計', '權益總計', '股本', '每股參考淨值']]
            for df in dfs if df.shape[1] > 10
        )

    def get_profit_lose(self, year, season):
        year = self._to_roc_year(year)
        url = 'https://mops.twse.com.tw/mops/web/t163sb04'
        dfs = self._fetch_from_url(url, year, season)
        rename_map = {
            '本期稅後淨利（淨損）': '本期淨利（淨損）',
            '其他綜合損益（稅後）': '其他綜合損益',
            '其他綜合損益（淨額）': '其他綜合損益',
            '其他綜合損益（稅後淨額）': '其他綜合損益',
            '本期其他綜合損益（稅後淨額）': '其他綜合損益',
            '本期綜合損益總額（稅後）': '本期綜合損益總額',
        }
        return pd.concat(
            df.rename(columns=rename_map)[['公司代號', '公司名稱', '本期淨利（淨損）', '其他綜合損益', '本期綜合損益總額']]
            for df in dfs if df.shape[1] > 10
        )

    def get_dividend(self, year):
        year = self._to_roc_year(year)
        url = 'https://mops.twse.com.tw/server-java/t05st09sub'
        form_data = {'step': 1, 'TYPEK': 'otc', 'qryType': 1, 'YEAR': year}
        r = requests.post(url, form_data)
        r.encoding = 'big5'
        dfs = pd.read_html(r.text, encoding='big-5')
        return pd.concat([df for df in dfs if 5 < df.shape[1] <= 20])


class StockAnalyzer:
    """Calculates key financial metrics for a given stock and year."""

    def __init__(self, stock_number):
        self.stock_number = stock_number
        self.report_fetcher = FinancialReportFetcher(stock_number)

    def _resolve_year_season(self, year):
        now = datetime.datetime.now()
        if year > now.year:
            raise Exception('year in the future')
        elif year < now.year:
            return 4, 12
        else:
            months = now.month - 1 if now.day > 15 else now.month - 2
            return months // 4, months

    def _get_value(self, df, *row_labels):
        col = df.columns[0]
        for label in row_labels:
            sheet = df[df[col] == label]
            if not sheet.empty:
                return sheet.values[0][1]
        raise ValueError(f"None of {row_labels} found in DataFrame")

    def calculate(self, year):
        season, months = self._resolve_year_season(year)
        fetch = self.report_fetcher.fetch

        # Balance sheet
        bs = fetch(year, season, 'BalanceSheet')
        equity  = (self._get_value(bs, '權益總額', '權益總計') + bs[bs[bs.columns[0]].isin(['權益總額', '權益總計'])].values[0][3]) / 2
        asset   = self._get_value(bs, '資產總額', '資產總計')
        liability = self._get_value(bs, '負債總額', '負債總計')
        share   = self._get_value(bs, '股本合計', '股本') / 10

        # Profit & loss
        pl = fetch(year, season, 'ProfitAndLose')
        netincome = self._get_value(pl, '本期淨利（淨損）', '本期稅後淨利（淨損）')
        eps = pl[pl[pl.columns[0]] == '基本每股盈餘'].values[1][1]

        # Dividend
        dividend_df = fetch(year, season, 'Dividend')
        dividend = dividend_df[dividend_df.columns[7]].values[0]

        # Holding share
        holding_df = fetch(year, months, 'HoldingShare')
        totalholding = self._get_value(holding_df, '全體董監持股合計') / 10

        # Average price
        stock = twstock.Stock(str(self.stock_number), False)
        price, total_day = 0, 0
        for month in range(1, months + 1):
            for data in stock.fetch(year, month):
                price += data.close
                total_day += 1
            time.sleep(1.0)
        average_price = price / total_day

        return {
            'ROE':                  netincome / equity,
            'dividend_payout_ratio': dividend / eps,
            'dividend_yield':        dividend / average_price,
            'PE_ratio':              average_price / eps,
            'debt_ratio':            liability / asset,
            'holding_ratio':         totalholding / share,
            'net_worth':             (asset - liability) / share,
        }


class TWSEDataFetcher:
    """Fetches daily trading reports from the Taiwan Stock Exchange open API."""

    API_URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"

    def get_stock_day_trading_report(self):
        report = requests.get(self.API_URL)
        if report.status_code == 200:
            date = datetime.datetime.strptime(
                report.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S %Z"
            )
            return date, report.json()
        return None
