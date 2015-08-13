import urllib
import pandas as pd
from pandas.io.data import DataReader
from datetime import datetime
import pdb
from diffs import *

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: performance.py <US/LSE> <yyyymmmdd>'
        sys.exit()

    market = sys.argv[1]
    if len(sys.argv) >= 3:
        asofDate = sys.argv[2]
    else:
        # Use last date from file
        dates = getDates(market)
        asofDate = dates[-1]

    portfolio = Portfolio()
    portfolio.readCsv(market + '-portfolio.csv')

    # Read symbols
    startDate = datetime(*getDateComponents(str(min([position.entryDate for position in portfolio.positions]))))
    endDate = datetime(*getDateComponents(str(asofDate)))

    pricesOpenFilename = 'open-prices-' + market + '.csv'
    pricesCloseFilename = 'close-prices-' + market + '.csv'

    DOWNLOAD = False
    if DOWNLOAD:
        # Download data
        i = 0
        for position in portfolio.positions:
            symbol = position.symbol
            allData = DataReader(symbol, 'yahoo', datetime(2000, 1, 1), endDate)
            print allData.tail(10)

            # Get open prices
            tsOpen = allData['Open']
            dataOpen = pd.DataFrame(list(tsOpen.values), index=tsOpen.index, columns=[symbol])
            if i == 0:
                pricesOpen = dataOpen
            else:
                pricesOpen = pd.concat([pricesOpen, dataOpen], axis=1)
            print pricesOpen.tail(10)

            # Get close prices
            tsClose = allData['Adj Close']
            dataClose = pd.DataFrame(list(tsClose.values), index=tsClose.index, columns=[symbol])
            if i == 0:
                pricesClose = dataClose
            else:
                pricesClose = pd.concat([pricesClose, dataClose], axis=1)
            print pricesClose.tail(10)

            i += 1

        startIndex = pricesOpen.index.searchsorted(startDate)
        pricesOpen = pricesOpen.ix[startIndex:]
        pricesOpen.to_csv(pricesOpenFilename)
        pricesClose = pricesClose.ix[startIndex:]
        pricesClose.to_csv(pricesCloseFilename)

    # Read data from file
    pricesOpen = pd.read_csv(pricesOpenFilename)
    pricesOpen = pricesOpen.set_index('Date')
    pricesOpen.index = pricesOpen.index.to_datetime()

    pricesClose = pd.read_csv(pricesCloseFilename)
    pricesClose = pricesClose.set_index('Date')
    pricesClose.index = pricesClose.index.to_datetime()

    POSITION_SIZE = 1000
    MARGIN = 0.05   # i.e. 5%
    #lastDate = pricesClose.index[-1]
    lastDate = datetime(2015, 8, 10)
    totEntryAmount = 0
    totCurrentAmount = 0
    totRetAmount = 0
    for position in portfolio.positions:
        symbol = position.symbol
        entryDate = datetime(*getDateComponents(str(position.entryDate)))
        nextOpenDate = pricesOpen.index.searchsorted(entryDate) + 1
        entryPrice = pricesOpen.ix[nextOpenDate][symbol]
        currentPrice = pricesClose.ix[lastDate][symbol]
        # For below calcs, see also lsepx.xlsx
        numShares = max(1, int(float(POSITION_SIZE) / float(entryPrice)))
        if position.direction == 'Short':
            multiplier = 1.0 - MARGIN
            direction = -1.0
        else:
            multiplier = 1.0
            direction = 1.0
        entryAmount = numShares * entryPrice * direction * multiplier
        currentAmount = numShares * currentPrice * direction * multiplier
        retAmount = (currentAmount - entryAmount) / multiplier
        ret = 100.0 * retAmount / entryAmount
        if position.direction == 'Short':
            ret = -ret
        print '%-8s %-5s %9s %9s %4d %8.2f %8.2f %8.2f %8.2f %8.2f %7.2f%%' % (
            symbol,
            position.direction,
            numShares,
            getMatchStr(str(position.entryDate)),
            0,
            entryPrice,
            currentPrice,
            entryAmount,
            currentAmount,
            retAmount,
            ret)

        totEntryAmount += entryAmount
        totCurrentAmount += currentAmount
        totRetAmount += retAmount
        totRet = 100.0 * totRetAmount / totEntryAmount

    print
    print '%8.2f %8.2f %8.2f %7.2f%%' % (totEntryAmount,
                                         totCurrentAmount,
                                         totRetAmount,
                                         totRet)
