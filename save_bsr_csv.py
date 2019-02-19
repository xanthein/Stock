#!/usr/bin/python3
import re

from scipy.misc import toimage
from pytesseract import image_to_string
import numpy as np
import cv2
import requests
from requests.adapters import HTTPAdapter
import time
from bs4 import BeautifulSoup
 
def clean_captcha(captcha):
    # Convert the image file to a Numpy array and read it into a OpenCV file.
    captcha = np.asarray(bytearray(captcha), dtype="uint8")
    captcha = cv2.imdecode(captcha, cv2.IMREAD_GRAYSCALE)
    
    # Convert the captcha to black and white.
    (thresh, captcha) = cv2.threshold(captcha, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    # Erode the image to remove dot noise and that wierd line. I use a 3x3 rectengal as the kernal.
    captcha = cv2.erode(captcha, np.ones((3, 3), dtype=np.uint8))
    
    # Convert the image to black and white and again to further remove noise.
    (thresh, captcha) = cv2.threshold(captcha, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    # Some cosmetic 
    captcha = cv2.fastNlMeansDenoising(captcha, h=50)
    
    # Turn the Numpy array back into a image
    captcha = toimage(captcha) 
    
    return captcha

def get_bsr_csv(stock):
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0'}
    rs = requests.session()

    scuess = 0
    while scuess == 0:

        try:
            page = rs.get('http://bsr.twse.com.tw/bshtm/bsMenu.aspx', headers=headers)
        except requests.exceptions.RequestException as e:
            print(e)
            time.sleep(2.0)
            continue

        if page.status_code != 200:
            time.sleep(2.0)
            continue
        # Get the capthca on TWSE's website. It's the second image on the page.
        soup = BeautifulSoup(page.content, 'html.parser')
        img_url = soup.findAll('img')[1]['src']
  
        # Request the captch
        try:
            img = requests.get('http://bsr.twse.com.tw/bshtm/' + img_url, headers=headers)
        except requests.exceptions.RequestException as e:
            print(e)
            time.sleep(2.0)
            continue
        if img.status_code == 200:
            img = img.content
        else:
            print('status code %s' % img.status_code)
            time.sleep(10.0)
            continue

        captcha = clean_captcha(img)
        captcha = re.sub('[^0-9A-Z]+', '', image_to_string(captcha).upper())

        payload = {
                '__EVENTTARET':"",
                '__EVENTARGUMENT':"",
                '__LASTFOCUS':"",
                'RadioButton_Normal':"RadioButton_Normal",
                'TextBox_Stkno':"",
                'CaptchaControl1':captcha,
                'btnOK':'查詢'
                }

        payload['TextBox_Stkno'] = str(stock)

        soup = BeautifulSoup(page.content, 'html.parser')
        for inp in soup.select("input[type==hidden]"):
            payload[inp['id']] = inp['value']

        try:
            page = rs.post('http://bsr.twse.com.tw/bshtm/bsMenu.aspx', data=payload, headers=headers)
        except requests.exceptions.RequestException as e:
            print(e)
            time.sleep(2.0)
            continue
        if page.status_code != 200:
            time.sleep(2.0)
            continue

        soup = BeautifulSoup(page.content, 'html.parser')
     
        if soup.select('span[id==Label_ErrorMsg]')[0].string == None:
            r1 = rs.get('http://bsr.twse.com.tw/bshtm/bsContent.aspx', headers=headers)
            scuess = 1
        else:
            time.sleep(2.0)
    
    return r1.content.decode(encoding='big5', errors='ignore')

def get_bsr_date():
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0'}
    rs = requests.session()
    while True:
        try:
            page = rs.get('http://bsr.twse.com.tw/bshtm/bsWelcome.aspx', headers=headers)
        except requests.exceptions.RequestException as e:
            print(e)
            continue
        if page.status_code == 200:
            soup = BeautifulSoup(page.content, 'html.parser')
            return soup.select('span[id==Label_Date]')[0].string.replace('/', '-')
        else:
            time.sleep(2.0)


