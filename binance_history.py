#import sqlite3    #Not required for this, but maybe in future to save to database instead
#import logging    #Not required yet, but maybe for logging on a bigger function
import time
import os
import math
import re
import csv
from datetime import datetime

from binance_api import Binance
import api_key

#Set up variables
API_KEY=api_key.API_ACCESS[0]
API_SECRET=api_key.API_ACCESS[1]
filename = 'hist.csv'
history_header=['Open time (milliseconds)',
                'Open',
                'High',
                'Low',
                'Close',
                'Volume',
                'Close time (milliseconds)',
                'Quote Asset Volume',
                '# Trades',
                'Taker buy base asset volume',
                'Taker buy quote asset volume',
                'Ignore']
bot = Binance(
    API_KEY,
    API_SECRET
)
hist_symbol='ETHUSDT'
hist_interval='1m'
hist_interval_val=int(re.search(r'\d+', hist_interval).group())
#Convert interval value to #minutes based on hours or days if required
if hist_interval[-1]=='h':
    hist_interval_val*=60
if hist_interval[-1]=='d':
    hist_interval_val*=1440
hist_step=60000*hist_interval_val*1000
#history from block setting (timestamps are milliseconds since 00:00:00 01 Jan 1970 UTC
hist_start=1546322400000   #01 Jan 2019-ish
hist_end=hist_start+hist_step-1
dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y (%H:%M)")
history_settings=f"Retrieved market data for {hist_symbol} at intervals of {hist_interval} as at {timestampStr}"

#Get the data
print('Retrieving market data for ETHUSDT')
with open(filename, 'w', newline='\n') as myfile:
     wr = csv.writer(myfile)
     wr.writerow([history_settings])    #[] wraps string in a list so it doesn't delimit the string as an array of characters
     wr.writerow(history_header)
i=1
while hist_end < 1576130400000:
    print(hist_symbol,hist_interval,hist_start,hist_end,'1576130400000')
    res = bot.klines(symbol=hist_symbol,
                     interval=hist_interval,
                     startTime=hist_start,
                     endTime=hist_end,
                     limit='1000')
    with open(filename, 'a', newline='\n') as myfile:
        wr = csv.writer(myfile)
        wr.writerows(res)
    hist_start+=hist_step
    hist_end+=hist_step
    i+=1
    
#Tell user it is done
print('Market data saved in hist.csv')
