# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 11:36:30 2024

@author: Srini

The code pulls Option chain OI summary and provides the max OI CE & PE 
strikes and the associated prices for Nifty, Bank Nifty and few 
highly traded companies. This will be a good snapshot to filter
for stocks & strikes (even for indices) that show promise
"""

### Import all the necessary libraries 
import json
import math
import datetime
import calendar
import requests
import yfinance as yf
import pandas as pd
from nsepython import nse_get_fno_lot_sizes

### urls to be referenced in code

url_oc      = "https://www.nseindia.com/option-chain"
url_bnf     = 'https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY'
url_nf      = 'https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY'
url_indices = "https://www.nseindia.com/api/allIndices"
url_eq      = "https://www.nseindia.com/api/option-chain-equities?symbol="

""" Defining the headers, sessions and initiating the cookies
to make connections """

headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
            'accept-language': 'en,gu;q=0.9,hi;q=0.8',
            'accept-encoding': 'gzip, deflate, br'}

sess = requests.Session()
cookies = dict()

""" Defining Methods to make API calls and ensuring the cookies are
persisted across sessions """

def set_cookie():
    request = sess.get(url_oc, headers=headers, timeout=60)
    cookies = dict(request.cookies)

def get_data(url):
    set_cookie()
    response = sess.get(url, headers=headers, timeout=60, cookies=cookies, stream = True)
    if(response.status_code==401):
        set_cookie()
        response = sess.get(url_nf, headers=headers, timeout=60, cookies=cookies, stream = True)
    if(response.status_code==200):
        return response.text
    return ""

""" Utility functions to get nearest strike price basis the last
price for both indices and stocks """

def round_nearest(x,num=50): return int(math.ceil(float(x)/num)*num)
def nearest_strike_bnf(x): return round_nearest(x,100)
def nearest_strike_nf(x): return round_nearest(x,100)
def get_nearest_strike_step_size_eq(data, expiry_date_monthly):
  if 'PE' in data['records']['data'][0]:
    ticker = data['records']['data'][0]['PE']['underlying']
  else:
    ticker = data['records']['data'][0]['CE']['underlying']
  ticker = ticker + '.NS'
  res_list = []
  info = yf.Ticker(ticker).info
  lprice = float(info['previousClose'])
  for item in data['records']['data']:
    if item['expiryDate'] == expiry_date_monthly:
       if lprice <= int(item['strikePrice']):
        res_list.append(int(item['strikePrice']))
        ind = data['records']['data'].index(item)
        res_list.append(int(data['records']['data'][ind + 2]['strikePrice']) - int(data['records']['data'][ind]['strikePrice'])) 
        return res_list

""" Code to extract monthly expriy date n months out """

def get_closest_monthly_expiry(expiry_date_list, num_of_months_out = 0):
      curr_day = datetime.date.today()
      year, month = curr_day.year, curr_day.month
      if month + num_of_months_out > 12:
        k = math.floor((month + num_of_months_out) / 12) # to get the num of years ahead
        month = (month + num_of_months_out) % 12 # to get the resultant month
        year = year + k 
      else:
        month = month + num_of_months_out
      
      lday = calendar.monthrange(year, month)[1]
      lday_month = datetime.date(year, month, lday)
      for i in expiry_date_list:
        if lday_month <= datetime.datetime.strptime(str(i), "%d-%b-%Y").date():
          return str(i)
      return str(epxiry_date_list[-1])

""" Code block to parse through option chain and get OI metrics """

def get_oi_metrics(url, nearest_strike = 0, step = 100, n = 20,  num_months_out = 0, ticker = ''):

  response_text = get_data(url)
  data = json.loads(response_text)
  expiry_dates_list = data['records']['expiryDates']
  expiry_date_monthly = get_closest_monthly_expiry(expiry_dates_list, num_months_out)
  if "NIFTY" not in url:
    reslist = get_nearest_strike_step_size_eq(data, expiry_date_monthly)
    nearest_strike = reslist[0]
    step = reslist[1]

  max_pe_oi = 0
  max_pe_oi_strike = 0
  max_pe_oi_price = 0
  max_ce_oi = 0
  max_ce_oi_strike = 0
  max_ce_oi_price = 0
  max_pe_oi_inc = 0
  max_pe_oi_inc_strike = 0
  max_pe_oi_inc_price = 0
  max_pe_oi_dec = 0
  max_pe_oi_dec_strike = 0
  max_pe_oi_dec_price = 0
  max_ce_oi_inc = 0
  max_ce_oi_inc_strike = 0
  max_ce_oi_inc_price = 0
  max_ce_oi_dec = 0 
  max_ce_oi_dec_strike = 0
  max_ce_oi_dec_price = 0
  underlying = ''
  output_row = []
  for item in data['records']['data']:
    if item['expiryDate'] == expiry_date_monthly:
      strike = int(item['strikePrice'])
      if strike >= (nearest_strike - (n * step)) & strike <= (nearest_strike + (n * step)):
        if 'PE' in item:
          pe_price = float(item['PE']['lastPrice'])
          underlying = item['PE']['underlying']
          if int(item['PE']['openInterest']) > max_pe_oi:
            max_pe_oi = int(item['PE']['openInterest'])
            max_pe_oi_strike = strike
            max_pe_oi_price = pe_price
          if int(item['PE']['changeinOpenInterest']) > max_pe_oi_inc:
            max_pe_oi_inc = int(item['PE']['changeinOpenInterest'])
            max_pe_oi_inc_strike = strike 
            max_pe_oi_inc_price = pe_price
          if int(item['PE']['changeinOpenInterest']) < max_pe_oi_dec:
            max_pe_oi_dec = int(item['PE']['changeinOpenInterest'])
            max_pe_oi_dec_strike = strike
            max_pe_oi_dec_price = pe_price
        if 'CE' in item:
          ce_price = float(item['CE']['lastPrice'])
          underlying = item['CE']['underlying']
          if int(item['CE']['openInterest']) > max_ce_oi:
            max_ce_oi = int(item['CE']['openInterest'])
            max_ce_oi_strike = strike 
            max_ce_oi_price = ce_price
          if int(item['CE']['changeinOpenInterest']) > max_ce_oi_inc:
            max_ce_oi_inc = int(item['CE']['changeinOpenInterest'])
            max_ce_oi_inc_strike = strike 
            max_ce_oi_inc_price = ce_price 
          if int(item['CE']['changeinOpenInterest']) < max_ce_oi_dec:
            max_ce_oi_dec = int(item['CE']['changeinOpenInterest'])
            max_ce_oi_dec_strike = strike 
            max_ce_oi_dec_price = ce_price
  
  if underlying == 'NIFTY':
    lot_size = 50
  else:
    #print('getting lot sizes')
    lot_size = nse_get_fno_lot_sizes(underlying)

  output_row.append(underlying)
  output_row.append(expiry_date_monthly)
  output_row.append(lot_size)
  output_row.append(max_pe_oi_strike)
  output_row.append(max_pe_oi_price)
  output_row.append(max_pe_oi)
  output_row.append(max_ce_oi_strike)
  output_row.append(max_ce_oi_price)
  output_row.append(max_ce_oi)
  output_row.append(max_pe_oi_inc_strike)
  output_row.append(max_pe_oi_inc_price)
  output_row.append(max_pe_oi_inc)
  output_row.append(max_ce_oi_inc_strike)
  output_row.append(max_ce_oi_inc_price)
  output_row.append(max_ce_oi_inc)
  output_row.append(max_pe_oi_dec_strike)
  output_row.append(max_pe_oi_dec_price)
  output_row.append(max_pe_oi_dec)
  output_row.append(max_ce_oi_dec_strike)
  output_row.append(max_ce_oi_dec_price)
  output_row.append(max_ce_oi_dec)

  return output_row

""" Main Code block that generates the OI summary and exports it"""

cols_list = ['Underlying', 'expiry_date',  'lot_size',  \
           'max_pe_oi_strike', 'max_pe_oi_price', 'max_pe_oi', \
           'max_ce_oi_strike', 'max_ce_oi_price', 'max_ce_oi', \
           'max_pe_oi_inc_strike', 'max_pe_oi_inc_price', 'max_pe_oi_inc', \
           'max_ce_oi_inc_strike', 'max_ce_oi_inc_price', 'max_ce_oi_inc', \
           'max_pe_oi_dec_strike', 'max_pe_oi_dec_price', 'max_pe_oi_dec', \
           'max_ce_oi_dec_strike', 'max_ce_oi_dec_price', 'max_ce_oi_dec']
response_text = get_data(url_indices)
data = json.loads(response_text)
for index in data["data"]:
  if index["index"]=="NIFTY 50":
    nf_ul = index["last"]
  if index["index"] == "NIFTY BANK":
    bnf_ul = index["last"]
nearest_strike_nifty = nearest_strike_nf(nf_ul)
bank_nifty_nearest_strike = nearest_strike_bnf(bnf_ul)
oi_df_list = []
nifty_oi_summary = get_oi_metrics(url_nf, nearest_strike_nifty)
bnf_oi_summary = get_oi_metrics(url_bnf, bank_nifty_nearest_strike)
oi_df_list.append(nifty_oi_summary)
oi_df_list.append(bnf_oi_summary)
eq_list = ['RELIANCE', 'SBIN', 'ASIANPAINT', 'ICICIBANK', 'HINDUNILVR', 'INFY', 'TCS', 'ONGC', 'IOC']
for e in eq_list:
  url_e = url_eq + e
  #print(url_e)
  eq_summary = get_oi_metrics(url_e)
  oi_df_list.append(eq_summary)
oi_df = pd.DataFrame(oi_df_list, columns = cols_list)
tnow = str(datetime.datetime.now())
tnow_list = tnow.split(' ')
tnow_date = tnow_list[0]
tnow_time_list = tnow_list[1].split(',')
tnow_time_list = tnow_time_list[0].split(':')
tnow_time_hr = tnow_time_list[0]
file_ts = tnow_date + '_' + tnow_time_hr
fname = 'C:/Users/Admin/Downloads/trade_data/oi_summary_files/options_oi_summary_' + file_ts + '.csv'
oi_df.to_csv(fname, sep = ',', index = False)






