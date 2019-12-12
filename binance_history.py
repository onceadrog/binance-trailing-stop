#import sqlite3    #Not required for this, but maybe in future to save to database instead
#import logging    #Not required yet, but maybe for logging on a bigger function
import time
import os
import math

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
dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y (%H:%M)")
history_settings=f"Retrieved market data for {hist_symbol} at intervals of {hist_interval} as at {timestampStr}"

#Get the data
print('Retrieving market data for ETHUSDT')
res = bot.klines(symbol=hist_symbol',
                     interval=hist_interval,
                     limit='1000')

#Output on screen (compressed block) and save to csv file
print('Market Result',res)
with open(filename, 'w', newline='\n') as myfile:
     wr = csv.writer(myfile)
     wr.writerow([history_settings])    #[] wraps string in a list so it doesn't delimit the string as an array of characters
     wr.writerow(history_header)
     wr.writerows(res)
