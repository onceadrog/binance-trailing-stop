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
import api_key

bot = Binance(
    API_KEY=api_key.API_KEY,
    API_SECRET=api_key.API_SECRET
)

settings = dict(
    symbol='BNBBTC',            # A pair for tracking
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

print('Retrieving market data for ETHUSDT')

res = bot.klines(symbol='ETHUSDT',
                     interval='1m',
                     limit='1000')
print('Market Result',res)

#linebreaks
#strip characters
#append to textstream object

