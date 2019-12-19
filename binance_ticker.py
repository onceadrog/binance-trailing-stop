#import sqlite3    #Not required for this, but maybe in future to save to database instead
#import logging    #Not required yet, but maybe for logging on a bigger function
import time
import os
import math
import re
import csv
import sys
import json
from datetime import datetime

from binance_api import Binance
import api_key

#Set up variables
API_KEY=api_key.API_ACCESS[0]
API_SECRET=api_key.API_ACCESS[1]
buy_min = 0.002
buy_max = 0.009
sell_min = 0.004
sell_max = 0.005
hist_symbol='BTCUSDT'
hist_interval='1m'

def ticker():
    res = bot.klines(symbol=hist_symbol,
                     interval=hist_interval,
                     limit='1')
    
    percent_change = (float(res[0][4])/float(res[0][1]))-1
    res[0].append(percent_change)
    res = res[0] #because 'res' normally returns many results as a nested list, instead of a single result
    buy_sell_hold,trade_volume = strat(res[5],percent_change,res[4])
    if trade_volume.isnumeric():
        trade_value = trade_volume * res[5]
        trade_volume = 'up to ${:6.4f} worth of {}'.format(trade_value,hist_symbol)
    buy_sell_hold = f'{buy_sell_hold} {trade_volume}'
    print('Open: {:8.2f}  Close: {:8.2f}  Volume: {:9.4f}  # Trades: {:4.0f}  Percent Change: {: 4.4%}'.format(float(res[1]),float(res[4]),float(res[5]),float(res[8]),percent_change),\
          f'Recommend: {buy_sell_hold}')
    res.append(buy_sell_hold)
    with open(filename, 'a', newline='\n') as myfile:
        wr = csv.writer(myfile)
        wr.writerows([res])
        
def strat(cur_volume,cur_percent,cur_close):
    if cur_percent >= buy_min and cur_percent <= buy_max:    #check if buy
        trade_volume = cur_volume/100 #limits trade to 1% of volume in last minute
        return 'buy',trade_volume
    else:
        if cur_percent >= -sell_max and cur_percent <=-sell_min:
            return 'sell','all'   #dropping in value
        else:
            return 'hold',''
    
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
                'Ignore',
                'Percent change',
                'Recommendation']
bot = Binance(
    API_KEY,
    API_SECRET
)

#Setup new history file
print('Retrieving market data for',hist_symbol,'at',hist_interval)
filename = f"./logs/ticker_{hist_symbol}.csv"
history_settings=f"Retrieved market data for {hist_symbol} at intervals of {hist_interval}"
with open(filename, 'w', newline='\n') as myfile:
     wr = csv.writer(myfile)
     wr.writerow([history_settings])    #[] wraps string in a list so it doesn't delimit the string as an array of characters
     wr.writerow(history_header)

while True:
    ticker()
    for x in range(60): #check each second for break
        time.sleep(1)

