#import sqlite3    #Not required for this, but maybe in future to save to database instead
#import logging    #Not required yet, but maybe for logging on a bigger function
import time
import os
import math
import re
import csv
import sys
from datetime import datetime
#import pandas (to instead use dataframes in future)

#strategy variables
hist_symbol = 'ETHUSDT'
balance = 10000
buy_min = 0.001
buy_max = 0.015
sell_min = 0.004
sell_max = 0.011
stop_loss_threshold = 0.95

def strat(cur_volume,cur_percent,cur_close):
    if cur_percent >= buy_min and cur_percent <= buy_max:    #check if buy
        trade_volume = cur_volume/100 #limits trade to 1% of volume in last minute
        return 'buy',trade_volume
    else:
        return 'hold',0

def review_trades(cur_close, cur_percent, stop_loss):
    if cur_close <= stop_loss: #price dropped to stop_loss threshold
        return 'stop'
    if cur_percent >= -sell_max and cur_percent <=-sell_min:
        return 'sell'   #dropping in value
    else:
        return 'hold'

#initialise variables
hist_smooth = 5
cur_trades=[]
buy_trades = 0
sell_trades = 0
missed_trades = 0
partial_trades = 0
stop_trades = 0
trade_value = 0
min_percent = 0
max_percent = 0
min_line = 0
held_balance = 0

#Iterate file
hist_fname = f"hist_{hist_symbol}.csv"
with open(hist_fname) as f_input, open('ledger.csv','w',newline='\n') as f_output, open('test_log.csv','a',newline='\n') as f_log:
    csv_input = csv.reader(f_input)
    csv_output = csv.writer(f_output)
    csv_log = csv.writer(f_log)
    csv_output.writerow(['cur_volume','cur_percent','cur_close','buy_sell_hold','trade_volume','balance'])
    line_count = 0     #use % (mod) line_count for array position for smoothed history
    print('Started logging to ledger.csv')
    print('Buy Min:  {:.2%}    Buy Max: {:.2%}'.format(buy_min,buy_max))
    print('Sell Min: {:.2%}    Sell Max: {:.2%}'.format(sell_min,sell_max))
    print('Stop Loss Threshold {:.0%}'.format(stop_loss_threshold))
    for row in csv_input:
        if line_count <=2:
            #skip 2x header rows
            line_count += 1
        if line_count == 3:
            cur_volume = float(row[3])
            cur_close = float(row[4])
            line_count += 1
        if line_count >= 4:
            hist_close = cur_close
            cur_volume = float(row[3])
            cur_close = float(row[4])
            if cur_close != 0:
                cur_percent = (cur_close - hist_close)/hist_close
            else:
                cur_percent = 0            
            buy_sell_hold, trade_volume = strat(cur_volume,cur_percent,cur_close)
            #log min/max percent for analysis
            if cur_percent < min_percent:
                min_percent = cur_percent
                min_line = line_count
            if cur_percent > max_percent:
                max_percent = cur_percent
            #append order to current orders
            if buy_sell_hold == 'buy':
                stop_loss = cur_close * stop_loss_threshold
                trade_value = cur_close * trade_volume
                if balance > 0:
                    buy_trades += 1
                    if trade_value > balance:   #don't spend more than you have
                        trade_value = balance
                        partial_trades += 1
                        balance -= trade_value
                        cur_trades.append([cur_close,trade_volume,stop_loss])
                    else:
                        balance -= trade_value
                        cur_trades.append([cur_close,trade_volume,stop_loss])
                else:
                    #don't trade
                    missed_trades += + 1
            if trade_value != 0:
                #print(f'buy value:{trade_value} balance:{balance}')
                trade_value = 0
            #review each trade still held
            result=[]
            for trade in cur_trades:
                if review_trades(cur_close,cur_percent,trade[2]) == 'sell':
                    #sell that trade, and don't store it to results of cur_trades
                    sell_trades += 1
                    balance += (cur_close*trade[1])
                    #print(f'sell value:{cur_close*trade[1]} balance:{balance}')
                else:
                    if review_trades(cur_close,cur_percent,trade[2]) == 'stop':
                        #sell that trade, and don't store it to results of cur_trades
                        balance += (cur_close*trade[1])
                        stop_trades += 1
                        #print(f'stop value:{cur_close*trade[1]} balance:{balance}')
                    else:
                        result.append(trade)  #store it for next check
            cur_trades = result  #store results back to trade list
            #output ledger
            #csv_output.writerow([cur_volume,"{:.2%}".format(cur_percent),cur_close,buy_sell_hold,trade_volume,"{:.2f}".format(balance)])
            line_count += 1
    #footer of trades still held and value
    held_trades = 0
    for trade in cur_trades:
        #print(trade)
        held_balance += (cur_close*trade[1])
        held_trades += 1
    print(f'Missed trades due to insufficient funds: {missed_trades} and {partial_trades} partial trades')
    print(f'Buy trades made: {buy_trades}     Sell trades made: {sell_trades}') 
    print(f'Stop loss trades made: {stop_trades}')
    print(f'Balance: {balance}')
    print(f'Balance of held trades: {held_balance} for {held_trades} trades')
    print('Min %: {:.2%}     Max %: {:.2%}'.format(min_percent,max_percent))
    print("Profit over the year: {:.2%}".format((balance+held_trades)/10000 - 1))
    #log to test_log.csv
    csv_log.writerow([hist_symbol,(balance+held_trades)/10000,balance,held_balance,held_trades,missed_trades,partial_trades,buy_trades,sell_trades,stop_trades,buy_min,buy_max,sell_min,sell_max,stop_loss_threshold])
    print('test_log.csv updated')
    
