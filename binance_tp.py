"""
    Detailed information about the bot on bablofil.ru/bot-dlya-binance
"""
import sqlite3
import logging
import time
import os
import math

from datetime import datetime

from binance_api import Binance

bot = Binance(
    API_KEY='',
    API_SECRET=''
)

settings = dict(
    symbol='EOSBTC',            # A pair for tracking
    strategy="Short",           # Strategy - Long (up), Short (down)           
    stop_loss_perc = 0.5,       # % remaining from the price
    stop_loss_fixed = 0,        # The initial stop-loss can be set by hand, then the bot will tighten.
                                # You can specify 0, then the bot will calculate, take the current price and apply a percentage to it
    amount = 0.0015             # Number of coins we plan to sell (in case of Long) or buy (in case of Short)
                                # If we specify Long, then the violas are for sale (e.g., sell 0.1 ETH in a pair of ETHBTCs)
                                # If Short, then the amount of money to buy, for example, to buy at 0.1 BTC on ETHBTC pair
)

multiplier = -1 if settings['strategy'] == "Long" else 1

print("Getting pairs' settings from the stock exchange")
symbols = bot.exchangeInfo()['symbols']
step_sizes = {symbol['symbol']:symbol for symbol in symbols}
for symbol in symbols:
    for f in symbol['filters']:
        if f['filterType'] == 'LOT_SIZE':
            step_sizes[symbol['symbol']] = float(f['stepSize'])


while True:
    try:
        print('Checking the pair {pair}, strategy {strategy}'.format(pair=settings['symbol'], strategy=settings['strategy'])
        # We're getting our current courses in pairs
        current_rates = bot.depth(symbol=settings['symbol'], limit=5)

        bid=float(current_rates['bids'][0][0])
        ask=float(current_rates['asks'][0][0])

        # If we play for a raise, we are guided by the prices at which they are sold, otherwise by the prices at which they are bought
        curr_rate = bid if settings['strategy'] == "Long" else ask
        
        if settings['stop_loss_fixed'] == 0:
           settings['stop_loss_fixed'] = (curr_rate/100) * (settings['stop_loss_perc']*multiplier+100)
 
        print("Current bid {bid:0.8f}, ask {ask:0.8f}, selected {cr:0.8f} stop_loss {sl:0.8f}".format(
            bid=bid, ask=ask, cr=curr_rate, sl=settings['stop_loss_fixed']
        ))

        # We think what would be the stop-loss if you applied it to %
        curr_rate_applied = (curr_rate/100) * (settings['stop_loss_perc']*multiplier+100)

        if settings['strategy'] == "Long":
            # Long strategy chosen, trying to sell coins as profitable as possible
            if curr_rate > settings['stop_loss_fixed']:
                print("Current price is higher than Stop-Loss price")
                if curr_rate_applied > settings['stop_loss_fixed']:
                    print("It's time to change the stop-loss, the new value {sl:0.8f}".format(sl=curr_rate_applied))                    
                    settings['stop_loss_fixed'] = curr_rate_applied
            else:
                # Current price is lower or equal to stop loss, market sale
                res = bot.createOrder(
                    symbol=settings['symbol'],
                    recvWindow=15000,
                    side='SELL',
                    type='MARKET',
                    quantity=settings['amount']
                )
                print('The result of the order creation', res)
                if 'orderId' in res:
                    # The creation of the order was a success, the exit
                    break
        else:
            # Short strategy chosen, trying to buy coins as profitable as possible
            if curr_rate < settings['stop_loss_fixed']:
                print("Current price is lower than stop-loss")
                if curr_rate_applied < settings['stop_loss_fixed']:
                    print("It's time to change the stop-loss, the new value {sl:0.8f}".format(sl=curr_rate_applied))                    
                    settings['stop_loss_fixed'] = curr_rate_applied
            else:
                # Price rises above Stop-Loss, Market Buying
                quantity = math.floor((settings['amount']/curr_rate)*(1/step_sizes[settings['symbol']]))/(1/step_sizes[settings['symbol']])
                print("Price rises above Stop-Loss, Market Buying, Coins {quantity:0.8f}".format(quantity=quantity))
                # math.Floor(coins*(1/stepSize)) / (1 / stepSize)
                res = bot.createOrder(
                    symbol=settings['symbol'],
                    recvWindow=15000,
                    side='BUY',
                    type='MARKET',
                    quantity=quantity
                )
                print('Order creation result', res)
                if 'orderId' in res:
                    # Creation of the order was successful, the exit
                    break

    except Exception as e:
        print(e)
    time.sleep(1)
#print(bot.myTrades(symbol='PPTETH'))
