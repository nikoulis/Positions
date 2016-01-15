import sys
from diffs import *
import os

#-------------------------
# Analyze daily portfolio
#-------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: analyze.py <US/LSE>'
        sys.exit()

    market = sys.argv[1]
    filename = market + '-sample.csv'
    portfolio = Portfolio(market)
    portfolio.readCsv(filename)
    stockInfoHash = readSectorFile(market)
    portfolio.showStats(stockInfoHash)
