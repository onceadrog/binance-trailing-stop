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
min_return = 0.01   #Only sell if you will make at least this much profit
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
#Set up bot for API calls
bot = Binance(
    API_KEY,
    API_SECRET
)
#Set up a list of symbol pairs to check, and wallet elements to show
#####
symbol='BTCUSDT' 
interval='1m'
    
def timestamp():
    ts = time.time()*1000
    ts -= 0 #timezone offset in milliseconds
    return ts

def ticker(symbol):
    #Kline call to API for history of last minute only
    res = bot.klines(symbol=symbol,
                     interval=interval,
                     limit='1')
    percent_change = (float(res[0][4])/float(res[0][1]))-1
    res[0].append(percent_change)
    res = res[0] #because 'res' normally returns many results as a nested list, instead of a single result

    #Check metrics against strategy
    buy_sell_hold,trade_volume = strat(symbol,res[5],percent_change,res[4])
    if trade_volume.isnumeric():
        trade_value = float(trade_volume) * res[5]
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
            BTC_bal = float(x["free"])+float(x["locked"])
            if symbol[0:3] == 'BTC':
                sell_bal = float(BTC_bal)
            if symbol[3:6] == 'BTC':
                buy_bal = float(BTC_bal)
        if x["asset"]=="USDT":
            USDT_bal = float(x["free"])+float(x["locked"])
            if symbol[0:3] == 'USD':
                sell_bal = float(USDT_bal)
            if symbol[3:6] == 'USD':
                buy_bal = float(USDT_bal)
        if x["asset"]=="ETH":
            ETH_bal = float(x["free"])+float(x["locked"])
            if symbol[0:3] == 'ETH':
                sell_bal = float(ETH_bal)
            if symbol[3:6] == 'ETH':
                buy_bal = float(ETH_bal)
        if x["asset"]=="BNB":
            BNB_bal = float(x["free"])+float(x["locked"])
            if symbol[0:3] == 'BNB':
                sell_bal = float(BNB_bal)
            if symbol[3:6] == 'BNB':
                buy_bal = float(BNB_bal)
        if x["asset"]=="AION":
            AION_bal = float(x["free"])+float(x["locked"])
            if symbol[0:4] == 'AION':
                sell_bal = float(AION_bal)

    #Beep based on buy_sell_hold, print on screen, and create order accordingly
    if buy_sell_hold == 'buy':
        winsound.Beep(frequency, duration1)
        time.sleep(0.2)
        winsound.Beep(frequency, duration1)
        print('BUY')
        print('BUY')
        print('BUY')
        print('BUY')
        #check vs min order for pair
        ####
        #res = bot.createOrder(symbol=symbol,recvWindow=15000,side='BUY',type='MARKET',quantity=trade_volume)       #Buying disabled until further testing
        #update wallet data
        ####
    else:
        if buy_sell_hold == 'sell' :
            winsound.Beep(frequency, duration2)
            #check vs min order for pair
            ####
            #res = bot.createOrder(symbol=symbol,recvWindow=15000,side='SELL',type='MARKET',quantity=trade_volume)     #Selling disabled until further testing
            print('SELL')
            print('SELL')
            print('SELL')
            print('SELL')
            #update wallet data
            ####

    #Print and log details
    #List wallet for pair and pair details
    rel_bal = '{:6.4f} {:9.7f} {:9.7f} {:9f}'.format(BTC_bal,ETH_bal,BNB_bal,AION_bal)
    print('{: <8}  {:>13.7f}  {:>13.7f}  {:>10.4f}   {: 4.0f}   {: 4.4%}  '.format(symbol,float(res[1]),float(res[4]),float(res[5]),float(res[8]),percent_change),\
        '{: <15}  {}    {:14.9f}  {:>14.9f}'.format(buy_sell_hold_text,rel_bal,buy_bal,sell_bal))
    #Log details to file
    buy_sell_hold = f'{buy_sell_hold} {trade_volume}'
    #print('Open: {:8.2f}  Close: {:8.2f}  Volume: {:9.3f}  # Trades: {:4.0f}  Percent Change: {: 4.4%}'.format(float(res[1]),float(res[4]),float(res[5]),float(res[8]),percent_change))
    res.append(buy_sell_hold)
    res.append(rel_bal)
    with open(filename, 'a', newline='\n') as myfile:
        wr = csv.writer(myfile)
        wr.writerows([res])
        
def strat(symbol,cur_volume,cur_percent,cur_close):
    #check pair for min volume and check wallet for balance tradable
    if cur_percent >= buy_min and cur_percent <= buy_max:    #check if buy
        trade_volume = str(float(cur_volume)/100) #limits trade to 1% of volume in last minute
        return 'buy',trade_volume
    else:
        if cur_percent >= -sell_max and cur_percent <=-sell_min:
            #check order history for whether min_profit is being met
            ####
            return 'sell','volume to sell'   #dropping in value, check volume based on symbol and wallet
        else:
            return 'hold',''

#Setup new history file
filename = f"./logs/ticker_{time.time()}.csv"

#with open(filename, 'w', newline='\n') as myfile:      #commented out to append instead
#     wr = csv.writer(myfile)
#     wr.writerow(history_header)
# Check open orders
res = bot.openOrders()
#### Do something with that
#print(res)

print('Pair:      Open:          Close:         Volume:   Trades:  %Change    Recommendation:  BTC:   ETH:      BNB:      AION:             Avail Buy:     Avail Sell:')

while True:
    #Check server time and set bot offset to counter any discrepency between server and local
    bot.shift_seconds = bot.time()['serverTime']/1000-time.time()
    #Get ticker to check specific pairs
    ticker('BTCUSDT')
    ticker('ETHUSDT')
    ticker('ETHBTC')
    ticker('BNBBTC')
    ticker('AIONBTC')
    print('-------------------------------------------------------------')
    for x in range(60): #check each second for break
        time.sleep(1)

