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
filename = 'pairs.csv'
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

symbols = bot.exchangeInfo()['symbols']
cur_pairs = {symbol['symbol']:symbol for symbol in symbols}

with open(filename, 'w', newline='\n') as myfile:
     wr = csv.writer(myfile)
     wr.writerow(cur_pairs)
