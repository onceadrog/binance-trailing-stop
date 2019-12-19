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
hist_symbol = 'BTCUSDT'
balance = 10000
buy_min = 0.002
buy_max = 0.009
sell_min = 0.004
sell_max = 0.005
stop_loss_threshold = 0.95
scrape_profit = 0.5         #withdraw profit %
scrape_threshold = 50000     #threshold of value to withdraw
scrape_percent = 0.25        #percentage of profit to scrape
fee_percent = 0.0005         #0.05%
spend_limit = 0.33           #only spend max 1/3 of available balance per buy

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
fees = 0
withdrawn = 0
withdrawals = 0
trade_volume_all = 0

#Iterate file
hist_fname = f"./logs/hist_{hist_symbol}.csv"
with open(hist_fname) as f_input, open('./logs/ledger.csv','w',newline='\n') as f_output, open('test_log.csv','a',newline='\n') as f_log:
    csv_input = csv.reader(f_input)
    csv_output = csv.writer(f_output)
    csv_log = csv.writer(f_log)
    csv_output.writerow(['line','cur_volume','cur_percent','cur_close','buy_sell_hold','trade_volume','balance','withdrawn','bought at','net trade profit'])
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
            cur_volume = float(row[5])
            cur_close = float(row[4])
            line_count += 1
        if line_count >= 4:
            hist_close = cur_close
            cur_volume = float(row[5])
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
                    if trade_value > balance * spend_limit:   #don't spend more than you have
                        trade_value = balance * spend_limit
                        partial_trades += 1
                        balance -= trade_value
                        cur_fees = trade_value * fee_percent 
                        trade_value -= cur_fees 
                        trade_volume = trade_value / cur_close 
                        fees += cur_fees 
                        cur_trades.append([cur_close,trade_volume,stop_loss])
                    else:
                        balance -= trade_value 
                        cur_fees = trade_value * fee_percent 
                        trade_value -= cur_fees 
                        trade_volume = trade_value / cur_close
                        fees += cur_fees 
                        cur_trades.append([cur_close,trade_volume,stop_loss])
                else:
                    #don't trade
                    missed_trades += + 1

            #output ledger
            csv_output.writerow([line_count,cur_volume,"{:.2%}".format(cur_percent),cur_close,buy_sell_hold,trade_volume,"{:.2f}".format(balance),withdrawn])

            #review each trade still held
            result=[]
            for trade in cur_trades:
                buy_sell_hold = review_trades(cur_close,cur_percent,trade[2])
                if buy_sell_hold == 'sell':
                    #sell that trade, and don't store it to results of cur_trades
                    scrape_value = 0
                    sell_trades += 1
                    trade_volume = trade[1]
                    cur_sell = cur_close*trade[1]
                    cur_fees = fee_percent * cur_sell
                    trade_profit = cur_sell/trade[0] - fee_percent
                    if trade_profit > scrape_profit:
                        scrape_value += (cur_sell - cur_fees)-(trade[0]*trade[1])  #only scrape from net profit
                    if scrape_value < scrape_threshold:
                        scrape_value = 0
                    else:
                        scrape_value *= scrape_percent
                        withdrawals += 1
                    withdrawn += scrape_value
                    balance += (cur_sell - cur_fees - scrape_value)
                    fees += cur_fees
                    trade_volume_all += trade[1]
                    net_profit = trade[0]*trade[1] - cur_sell - cur_fees
                    csv_output.writerow([line_count,cur_volume,"{:.2%}".format(cur_percent),cur_close,buy_sell_hold,trade_volume,"{:.2f}".format(balance),withdrawn, trade[0],net_profit])
                    #print(f'sell value:{cur_close*trade[1]} balance:{balance}')
                else:
                    if buy_sell_hold == 'stop':
                        #sell that trade, and don't store it to results of cur_trades
                        trade_volume += trade[1]
                        cur_sell = cur_close*trade[1]
                        cur_fees = fee_percent * cur_sell
                        balance += (cur_sell - cur_fees)
                        fees += cur_fees
                        trade_volume_all += trade_volume
                        balance += (cur_close*trade[1])
                        stop_trades += 1
                        net_profit = trade[0]*trade[1] - cur_sell - cur_fees
                        #print(f'stop value:{cur_close*trade[1]} balance:{balance}')
                        csv_output.writerow([line_count,cur_volume,"{:.2%}".format(cur_percent),cur_close,buy_sell_hold,trade_volume,"{:.2f}".format(balance),withdrawn,trade[0],net_profit])
                    else:
                        result.append(trade)  #store it for next check
                    
            cur_trades = result  #store results back to trade list
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
    print(f'Balance: {balance}   Cash withdrawn: {withdrawn}')
    print(f'Balance of held trades: {held_balance} for {held_trades} trades')
    print('Min %: {:.2%}     Max %: {:.2%}'.format(min_percent,max_percent))
    print("Profit over the year: {:.2%}".format((balance + held_trades + withdrawn)/10000 - 1))
