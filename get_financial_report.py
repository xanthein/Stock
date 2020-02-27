#!/usr/bin/python3
import sys
import requests
import pandas as pd
import twstock
import time
import datetime
from bs4 import BeautifulSoup


def financial_report(stock_number, year, season, type='BalanceSheet'):

    if type == 'BalanceSheet':
        url = "https://mops.twse.com.tw/mops/web/ajax_t164sb03"; # 資產負債表
    elif type == 'ProfitAndLose':
        url = "https://mops.twse.com.tw/mops/web/ajax_t164sb04"; # 損益表
    elif type == 'CashFlowStatement':
        url = "https://mops.twse.com.tw/mops/web/ajax_t164sb05"; # 現金流量表
    elif type == 'Dividend': 
        url = "https://mops.twse.com.tw/mops/web/ajax_t05st09"; # 股利
    elif type == 'Revenu':
        url = "https://mops.twse.com.tw/mops/web/ajax_t05st10_ifrs"; # 營收
    elif type == 'HoldingShare': 
        url = "https://mops.twse.com.tw/mops/web/ajax_stapap1"; # 董監持股

    if year >= 1000:
        year -= 1911
    
    form_data = {
        'encodeURIComponent':1,
        'step':1,
        'firstin':1,
        'off':1,
        'TYPEK':'all',
        'co_id':stock_number,
        'isnew':'false',
        'year':year,
        'season':season,
    }

    if type == 'HoldingShare' or type == 'Revenu':
        form_data.pop('season', None)
        form_data['month'] = "%02d" % season

    r = requests.post(url, form_data)
    soup = BeautifulSoup(r.text, 'html.parser')
    if soup.select('input[type=button]') is not None:
        form_data['step'] = 2
        r = requests.post(url, form_data)
    if type == 'HoldingShare':
        html_df = pd.read_html(r.text)[4].fillna("")
    else:
        html_df = pd.read_html(r.text)[1].fillna("")
    return html_df

def get_revenu(year, month):
    if year > 1911:
        year -= 1911

    url = 'https://mops.twse.com.tw/nas/t21/sii/t21sc03_'+str(year)+'_'+str(month)+'_0.html'
    if year <= 98:
        url = 'https://mops.twse.com.tw/nas/t21/sii/t21sc03_'+str(year)+'_'+str(month)+'.html'

    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

    r = requests.get(url, headers=headers)
    r.encoding = 'big5'

    dfs = pd.read_html(r.text, encoding='big-5')

    df = pd.concat([df for df in dfs if df.shape[1] <= 11 and df.shape[1] > 5])

    if 'levels' in dir(df.columns):
        df.columns = df.columns.get_level_values(1)
    else:
        df = df[list(range(0,10))]
        column_index = df.index[(df[0] == '公司代號')][0]
        df.columns = df.iloc[column_index]

    df['當月營收'] = pd.to_numeric(df['當月營收'], 'coerce')
    df = df[~df['當月營收'].isnull()]
    df = df[df['公司代號'] != '合計']

    return df

def get_balance_sheet(year, season):
    if year > 1911:
        year -= 1911

    url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb05'

    form_data = {
        'encodeURIComponent':1,
        'step':1,
        'firstin':1,
        'off':1,
        'isQuery':'Y',
        'TYPEK':'sii',
        'year':year,
        'season':season,
    }

    r = requests.post(url, form_data)

    dfs = pd.read_html(r.text)

    df = pd.concat(df.rename(columns={'資產總額':'資產總計', '負債總額':'負債總計', '權益總額':'權益總計'})[['公司代號', '公司名稱', '資產總計', '負債總計', '權益總計', '股本', '每股參考淨值']] for df in dfs if df.shape[1] > 10)

    return df

def financial_report_all(year, season, type='BalanceSheet'):
    if type == 'BalanceSheet':
        url = ""; # 資產負債表
    elif type == 'ProfitAndLose':
        url = ""; # 損益表
    elif type == 'CashFlowStatement':
        url = ""; # 現金流量表
    elif type == 'Dividend':
        url = ""; # 股利
    elif type == 'HoldingShare':
        url = ""; # 董監持股

    if year >= 1000:
        year -= 1911

    form_data = {
        'encodeURIComponent':1,
        'step':1,
        'firstin':1,
        'off':1,
        'TYPEK':'all',
        'co_id':stock_number,
        'isnew':'false',
        'year':year,
        'season':season,
    }


def calculate_stock_info(stock_number, year):
    if year > datetime.datetime.now().year:
        raise Exception('year in the future')
    elif year < datetime.datetime.now().year:
        season = 4
        months = 12
    else:
        if datetime.datetime.now().day > 15:
            months = datetime.datetime.now().month - 1
        else:
            months = datetime.datetime.now().month - 2
        season = months // 4

    balancesheet = financial_report(stock_number, year, season, 'BalanceSheet')
    equity_sheet = balancesheet[balancesheet[balancesheet.columns[0]] == '權益總額']
    if equity_sheet.empty:
        equity_sheet = balancesheet[balancesheet[balancesheet.columns[0]] == '權益總計']
    equity = (equity_sheet.values[0][1] + equity_sheet.values[0][3])/2
    asset_sheet = balancesheet[balancesheet[balancesheet.columns[0]] == '資產總額']
    if asset_sheet.empty:
        asset_sheet = balancesheet[balancesheet[balancesheet.columns[0]] == '資產總計']
    asset = asset_sheet.values[0][1]
    liability_sheet = balancesheet[balancesheet[balancesheet.columns[0]] == '負債總額']
    if liability_sheet.empty:
        liability_sheet = balancesheet[balancesheet[balancesheet.columns[0]] == '負債總計']
    liability = liability_sheet.values[0][1]
    share_sheet = balancesheet[balancesheet[balancesheet.columns[0]] == '股本合計']
    if share_sheet.empty:
        share_sheet = balancesheet[balancesheet[balancesheet.columns[0]] == '股本']
    share = share_sheet.values[0][1] / 10
    profitandlose = financial_report(stock_number, year, season, 'ProfitAndLose')
    netincome_sheet = profitandlose[profitandlose[profitandlose.columns[0]] == '本期淨利（淨損）']
    if netincome_sheet.empty:
        netincome_sheet = profitandlose[profitandlose[profitandlose.columns[0]] == '本期稅後淨利（淨損）']
    netincome = netincome_sheet.values[0][1]
    eps = profitandlose[profitandlose[profitandlose.columns[0]] == '基本每股盈餘'].values[1][1]
    cashflowstatement = financial_report(stock_number, year, season, 'CashFlowStatement')
    stockdividend = financial_report(stock_number, year, season, 'Dividend')
    dividend = stockdividend[stockdividend.columns[7]].values[0]
    holdingshare = financial_report(stock_number, year, months, 'HoldingShare')
    totalholding = holdingshare[holdingshare[holdingshare.columns[0]] == '全體董監持股合計'].values[0][1]/10

    stock = twstock.Stock(str(stock_number), False)
    price = 0
    total_day = 0
    for month in range(1, months+1):
        month_data = stock.fetch(year, month)
        for data in month_data:
            price += data.close
            total_day+=1
        time.sleep(1.0)
    average_price = price/total_day

    ROE = netincome / equity
    dividend_payout_ratio = dividend / eps
    dividend_yield = dividend / average_price
    PE_ratio = average_price / eps
    debt_ratio = liability / asset
    holding_ratio = totalholding / share

    return ROE, dividend_payout_ratio, dividend_yield, PE_ratio, debt_ratio, holding_ratio


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(sys.argv[0]+' <stock number> <year>')
        sys.exit()
    
    stock_number = int(sys.argv[1])
    year = int(sys.argv[2])
    ROE, dividend_payout_ratio, dividend_yield, PE_ratio, debt_ratio, holding_ratio = calculate_stock_info(stock_number, year)

    print('ROE')
    print(ROE)
    print('配息率')
    print(dividend_payout_ratio)
    print('殖利率')
    print(dividend_yield)
    print('本益本')
    print(PE_ratio)
    print('負債比')
    print(debt_ratio)
    print('董監持股')
    print(holding_ratio)



