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
import winsound

from binance_api import Binance
import api_key

frequency = 1500  # Set Frequency To 2500 Hertz
duration1 = 400  # Set Duration To 1000 ms == 1 second
duration2 = 1000

#Set up variables
API_KEY=api_key.API_ACCESS[0]
API_SECRET=api_key.API_ACCESS[1]
buy_min = 0.002
buy_max = 0.009
sell_min = 0.004
sell_max = 0.005

#Set up a list of symbol pairs to check, and wallet elements to show
#####
hist_symbol='BTCUSDT' 
hist_interval='1m'
    
def timestamp():
    ts = time.time()*1000
    ts -= 0 #timezone offset in milliseconds
    return ts

def ticker(hist_symbol):
    #Kline call to API for history of last minute only
    res = bot.klines(symbol=hist_symbol,
                     interval=hist_interval,
                     limit='1')
    percent_change = (float(res[0][4])/float(res[0][1]))-1
    res[0].append(percent_change)
    res = res[0] #because 'res' normally returns many results as a nested list, instead of a single result

    #Check metrics against strategy
    buy_sell_hold,trade_volume = strat(res[5],percent_change,res[4])
    if trade_volume.isnumeric():
        trade_value = float(trade_volume) * res[5]
        trade_volume = 'up to ${:6.4f} worth of {}'.format(trade_value,hist_symbol)
    buy_sell_hold_text = f'{buy_sell_hold} {trade_volume}'

    #Check wallet       ####Rewrite for flexibility
    acc = bot.account()
    #print (acc,type(acc))  #acc also contains current fees,etc
    wal = acc.get("balances")
    #print (wal,type(wal))
    #Check which balances to list
    buy_bal = 0
    sell_bal = 0
    for x in wal:
        #print (x["asset"],x["free"],x["locked"])
        if x["asset"]=="BTC":
            BTC_bal = float(x["free"])
            if hist_symbol[0:3] == 'BTC':
                sell_bal = BTC_bal
            if hist_symbol[3:6] == 'BTC':
                buy_bal = BTC_bal
        if x["asset"]=="USDT":
            USDT_bal = float(x["free"])
            if hist_symbol[0:3] == 'USD':
                sell_bal = USDT_bal
            if hist_symbol[3:6] == 'USD':
                buy_bal = USDT_bal
        if x["asset"]=="ETH":
            ETH_bal = float(x["free"])
            if hist_symbol[0:3] == 'ETH':
                sell_bal = ETH_bal
            if hist_symbol[3:6] == 'ETH':
                buy_bal = ETH_bal
        if x["asset"]=="BNB":
            BNB_bal = float(x["free"])
            if hist_symbol[0:3] == 'BNB':
                sell_bal = BNB_bal
            if hist_symbol[3:6] == 'BNB':
                buy_bal = BNB_bal     

    #Beep based on buy_sell_hold, print on screen, and create order accordingly
    if buy_sell_hold == 'buy':
        winsound.Beep(frequency, duration1)
        time.sleep(0.2)
        winsound.Beep(frequency, duration1)
        print('BUY')
        print('BUY')
        print('BUY')
        print('BUY')
        #res = bot.createOrder(symbol=settings['hist_symbol'],recvWindow=15000,side='BUY',type='MARKET',quantity=settings['buy_bal'])       #Buying disabled until further testing
    else:
        if buy_sell_hold == 'sell' :
            winsound.Beep(frequency, duration2)
            #res = bot.createOrder(symbol=settings['hist_symbol'],recvWindow=15000,side='SELL',type='MARKET',quantity=settings['sell_bal'])     #Selling disabled until further testing
            print('SELL')
            print('SELL')
            print('SELL')
            print('SELL')

    #Print and log details
    #List wallet for pair and pair details
    rel_bal = 'BTC: {:4.4f}  ETH: {:0.7f}  BNB: {:0.7f}'.format(BTC_bal,ETH_bal,BNB_bal)
    print('{: <8} Open: {:4.7f}  Close: {:4.7f}  Volume: {:9.4f}  # Trades: {:4.0f}  Change: {: 4.4%}'.format(hist_symbol,float(res[1]),float(res[4]),float(res[5]),float(res[8]),percent_change))
    print('Recommend: {}   {}    {} Buy Bal: {}  Sell Bal: {}'.format(hist_symbol,buy_sell_hold_text,rel_bal,buy_bal,sell_bal))
    #Log details to file
    res.append(buy_sell_hold)
    res.append(BTC_bal)
    with open(filename, 'a', newline='\n') as myfile:
        wr = csv.writer(myfile)
        wr.writerows([res])
        
def strat(cur_volume,cur_percent,cur_close):
    if cur_percent >= buy_min and cur_percent <= buy_max:    #check if buy
        trade_volume = str(float(cur_volume)/100) #limits trade to 1% of volume in last minute
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
#with open(filename, 'w', newline='\n') as myfile:      #commented out to append instead
#     wr = csv.writer(myfile)
#     wr.writerow([history_settings])    #[] wraps string in a list so it doesn't delimit the string as an array of characters
#     wr.writerow(history_header)

while True:
    ticker('BTCUSDT')
    ticker('ETHUSDT')
    ticker('ETHBTC')
    ticker('BNBBTC')
    print('-------------------------------------------------------------')
    for x in range(60): #check each second for break
        time.sleep(1)

