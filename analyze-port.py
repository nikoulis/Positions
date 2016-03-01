import sys
from diffs import *
import os

#-------------------------
# Analyze daily portfolio
#-------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: analyze-port.py <US/LSE> <yyyymmdd>'
        sys.exit()

    market = sys.argv[1]
    dates = getDates(market)
    numDates = len(dates)
    if len(sys.argv) >= 3:
        date = sys.argv[2]

    FULL = True
    if FULL:
        startDateIndex = 0
    else:
        startDateIndex = dates.index(20150817)

    stockInfoHash = readSectorFile(market)
    # Start from empty portfolio, then update
    for i in range(startDateIndex, numDates):
        date = dates[i]
        print date
        portfolio = readPortfolio(market, date, 'Yahoo')
        portfolio.showStats(stockInfoHash)
