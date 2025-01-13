#!/usr/bin/python3

import requests
from bs4 import BeautifulSoup

tse_url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
otc_url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=4"

def getStockCode():
    page = requests.get(tse_url)
    soup = BeautifulSoup(page.content.decode('cp950'), 'html.parser')
    trs = soup.find_all('tr')
    content = []
    for tr in trs[1:]:
        if len(tr) < 2:
            continue
        if tr.contents[5].text == 'ESVUFR':
            content.append('%s,%s'%(tr.contents[0].text[:4], tr.contents[0].text[5:]))

    return content

def SaveCSV(data, filename):
    with open(filename, 'wb') as csvfile:
        content = '\r\n'.join(row for row in data)
        csvfile.write(content.encode('utf-8'))
        print("write %s ok."%(filename))

if __name__ == '__main__':
    SaveCSV(getStockCode(), 'stock.csv')
