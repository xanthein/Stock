#!/usr/bin/python3
import re

from scipy.misc import toimage
from pytesseract import image_to_string
import numpy as np
import cv2
import requests
import time
from bs4 import BeautifulSoup
 
def request_captcha(page):    
    base_url = 'http://bsr.twse.com.tw/bshtm/'
    # Get the capthca on TWSE's website. It's the second image on the page.
    soup = BeautifulSoup(page.content, 'html.parser')
    img_url = soup.findAll('img')[1]['src']
    
    # Request the captch and write it to disk.
    img = requests.get(base_url + img_url)
    if img.status_code == 200:
        img = img.content
    else:
        print('error')

    return img

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
    rs = requests.session()
    page = rs.get('http://bsr.twse.com.tw/bshtm/bsMenu.aspx')

    scuess = 0
    while scuess == 0:
        captcha = clean_captcha(request_captcha(page))
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

        page = rs.post('http://bsr.twse.com.tw/bshtm/bsMenu.aspx', data=payload)
        soup = BeautifulSoup(page.content, 'html.parser')
      
        if soup.select('span[id==Label_ErrorMsg]')[0].string == None:
            r1 = rs.get('http://bsr.twse.com.tw/bshtm/bsContent.aspx')
            scuess = 1
        else:
            time.sleep(0.5)
    
    return r1.content.decode(encoding='big5', errors='ignore')

def get_bsr_date():
    page = requests.get('http://bsr.twse.com.tw/bshtm/bsWelcome.aspx')
    soup = BeautifulSoup(page.content, 'html.parser')
    return soup.select('span[id==Label_Date]')[0].string.replace('/', '-')
