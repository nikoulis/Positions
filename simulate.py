import sys
sys.path.append('/home/nikoulis/anaconda/lib/python2.7/site-packages')  # For Ubuntu
from diffs import *
import os

#-------------------------------------------------------------
# Read the daily diffs file and update portfolio from scratch
#-------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: simulate.py <US/LSE>'
        sys.exit()

    market = sys.argv[1]
    dates = getDates(market)
    numDates = len(dates)
    if len(sys.argv) >= 3:
        asofDate = sys.argv[2]
    else:
        # Use last date from file
        asofDate = dates[-1]

    currentDate = int(time.strftime('%Y%m%d'))

    # Don't run if it's a holiday
    filename = getMarket(market) + '-holidays.csv'
    f = open(filename)
    for line in f:
        date = int(line.strip())
        if date == currentDate:
            print str(currentDate) + ' is a holiday.'
            sys.exit()

    FULL = False
    if FULL:
        startDateIndex = 0
    else:
        if market == 'US':
            startDateIndex = dates.index(20151006)
        elif market == 'LSE':
            startDateIndex = dates.index(20150922)
        elif market == 'US-tradehero':
            startDateIndex = dates.index(20151022)
        elif market == 'LSE-tradehero':
            startDateIndex = dates.index(20151022)

    # Start from empty portfolio, then update
    portfolio = Portfolio(market)
    for i in range(startDateIndex, numDates - 1):
        dailyPortfolio = Portfolio(market)
        print 'Updating for', dates[i + 1]
        filename = market + '-diffs-' + str(dates[i + 1]) + '.csv'
        if not os.path.exists(filename):
            calcDiffs(market, dates[i], str(dates[i + 1]), 'Yahoo')
        portfolio.update(dates[i + 1], display=True)
