import time
import os
import math
import re
import csv
import sys
import multiprocessing
from datetime import datetime
#import pandas (to instead use dataframes in future)
#pool = multiprocessing.Pool(processes=3)  #ref: http://earthpy.org/speed.html

#strategy variables
hist_symbol = 'ETHUSDT'
stop_loss_threshold = 0.95  #to amend risk appetite
start_balance = 10000
#ranges to test divide by 1000 to get 0.1 percent
#note: largest number is not reached. [1,10] = 1-9 tested
#300 options with current settings
buy_min_range = [1,4]
buy_max_range = [5,10]
sell_min_range = [1,5]
sell_max_range = [5,10]

def strat(cur_volume,cur_percent,cur_close):
    if cur_percent >= buy_min and cur_percent <=buy_max:    #check if buy
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
max_profit = [0,0,0,0,0,0]
iterations_tested = 0

#Iterate file
hist_fname = f"hist_{hist_symbol}.csv"
with open(hist_fname) as f_input, open('ledger.csv','w',newline='\n') as f_output:
    csv_input = csv.reader(f_input)
    csv_output = csv.writer(f_output)
    header_text = ['Currency pair','Profit %','Balance','Held balance','Held trades','Missed trades','Partial trades','Buy trades','Sell trades','Stop trades','Stop trade %','Buy min','Buy max','Sell min','Sell max','Stop loss threshold']
    csv_output.writerow(header_text)
    line_count = 0     #use % (mod) line_count for array position for smoothed history
    print('Started logging to ledger.csv')
    #iterate ranges of inputs
    for buy_min_i in range(*buy_min_range):
        for buy_max_i in range(*buy_max_range):
            for sell_min_i in range(*sell_min_range):
                for sell_max_i in range(*sell_max_range):
                    iterations_tested += 1
                    buy_min = buy_min_i/1000
                    buy_max = buy_max_i/1000
                    sell_min = sell_min_i/1000
                    sell_max = sell_max_i/1000
                    #set/reset per iteration variables
                    balance = start_balance
                    f_input.seek(2)
                    line_count = 0
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
                    held_balance = 0
                    for trade in cur_trades:
                            held_balance += (cur_close*trade[1])
                            held_trades += 1
                    profit = (balance + held_balance)/10000 - 1
                    #store max profit settings
                    if profit > max_profit[0]:
                            max_profit = [profit,buy_min,buy_max,sell_min,sell_max,stop_loss_threshold]
                    #log run
                    stop_trade_percent = stop_trades/sell_trades
                    log_data = [hist_symbol,'{:.2%}'.format(profit),'{:.4f}'.format(balance),'{:.4f}'.format(held_balance),\
                                held_trades,missed_trades,partial_trades,buy_trades,sell_trades,stop_trades,'{:.2%}'.format(stop_trade_percent),\
                                '{:.2%}'.format(buy_min),'{:.2%}'.format(buy_max),'{:.2%}'.format(sell_min),'{:.2%}'.format(sell_max),\
                                '{:.1%}'.format(stop_loss_threshold)]
                    print(*log_data)
                    csv_output.writerow(log_data)
        
#Output max profit settings
print(f'Last profit: {profit},{balance},{held_balance}')
print(f'Max Profit: {max_profit[0]}')
print(f'Buy Minimum: {max_profit[1]} Buy Maximum: {max_profit[2]}')
print(f'Sell Minimum: {max_profit[3]} Buy Maximum: {max_profit[4]}')
print(f'Stop loss: {max_profit[5]}')
print(f'{iterations_tested} combinations tested')
