import glob
import os
import sys
import pdb
import time
import random
from diffs import *
from sectors import *
from pandas.io.data import DataReader
from datetime import datetime

#------------------------------------------------
# Read two portfolios and find their differences
#------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: parse.py <US/LSE> <yyyymmdd1> <yyyymmdd2>'
        sys.exit()

    market = sys.argv[1]
    if market == 'US':
        fileMarketIndic = 'P '
    else:
        fileMarketIndic = 'LSE '

    # 1. Read today's and yesterday's benchmark portfolio and find diffs
    if len(sys.argv) >= 4:
        # Use specified dates to determine filenames
        filenameYesterday = glob.glob('c:/mails/*_ ' + fileMarketIndic + getMatchStr(sys.argv[2]) + '.txt')[0]
        filenameToday = glob.glob('c:/mails/*_ ' + fileMarketIndic + getMatchStr(sys.argv[3]) + '.txt')[0]
    else:
        # Use the two latest filenames (based on time created) for this market
        filenameList = sorted(glob.glob('c:/mails/*_ ' + fileMarketIndic + '*.txt'))
        numFiles = len(filenameList)
        filenameYesterday = filenameList[numFiles - 2]
        filenameToday = filenameList[numFiles - 1]

    source = 'Outlook'
    market = sys.argv[1]
    dateYesterday = sys.argv[2]
    dateToday = sys.argv[3]
    portfolioYesterday = readPortfolio(market, dateYesterday, source)
    portfolioToday = readPortfolio(market, dateToday, source)
    diffs = Diffs(portfolioYesterday, portfolioToday)

    print 'New:'
    for position in diffs.newPositions:
        print position
    print
    print 'Removed:'
    for position in diffs.removedPositions:
        print position
    
    SAMPLE = True
    if SAMPLE:
        # 1. Read sector data
        f = open('allsectors.csv')
        stockSector = {}
        for line in f:
            data = line.strip().split(',')
            stockSector[data[0]] = data[1]
        f.close()

        # 2. Update sector data with new positions
        f = open('allsectors.csv', 'a')
        for position in diffs.newPositions:
            name, marketCap, sector, industry = getYahooFinanceData(position.symbol)
            marketCapNum = getMarketCapNum(marketCap)
            print position.symbol, name, marketCap, marketCapNum, sector, industry
            if stockSector.get(position.symbol) == None:
                stockSector[position.symbol] = sector
                f.write(position.symbol + ',' + sector + ',' + str(marketCapNum) + '\n')
        f.close()

        # 3. Calculate sector percentages in benchmark portfolio
        sectorPositions, sectorPercent = calcSectorPercent(portfolioToday, stockSector)
        targetNumStocks = {}
        for sectorName in sectorPercent.keys():
            targetNumStocks[sectorName] = max(1, int(sectorPercent[sectorName]))
            print sectorName, ':', sectorPercent[sectorName], targetNumStocks[sectorName]

        # 4. Calculate sector percentages in sample portfolio
        #f = open('sample.csv', 'a')
        #samplePortfolio = Portfolio()
        #for line in f:
        #    data = line.strip(s).split(',')
        #    position = Position(data[0], data[1])
        #    samplePortfolio.positions.append(position)
        #sampleSectorPositions, sampleSectorPercent = calcSectorPercent(portfolio, stockSector)

        # 5. Pick new stocks to include in sample portfolio so that percentages get closer
        for position in portfolioToday.positions:
            pass

    CHECK = False
    if CHECK:
        # Check daily portfolio creation process
        filenameList = sorted(glob.glob('c:/mails/*_ ' + fileMarketIndic + '*.txt'))
        print filenameList

        # Initialize running portfolio
        openDate = {}
        filename = filenameList[0]
        runningPortfolio = readPortfolio(filename, market)
        for position in runningPortfolio.positions:
            date = filename[filename.find(fileMarketIndic) + len(fileMarketIndic):filename.find('.txt')]
            openDate[position.symbol] = getStdStr(date)
            print position, openDate[position.symbol]

        # Now check all dates one by one
        for i in range(1, len(filenameList)):
            filenameYesterday = filenameList[i - 1]
            filenameToday = filenameList[i]
            diffs = findDiffs(filenameYesterday, filenameToday, market)

            #print 'New:'
            #for position in diffs.newPositions:
            #    print position

            # Get a sample of positions to include in portfolio (usually 1 position, unless newPositions >= 20)
            numNewPositions = len(diffs.newPositions)
            minNumSamplePositions = 1
            #sampleSize = max(minNumSamplePositions, numNewPositions / 10)
            sampleSize = numNewPositions
            sampleIndices = sorted(random.sample(xrange(numNewPositions), min(sampleSize, numNewPositions)))
            samplePositions = [diffs.newPositions[i] for i in sampleIndices]
            runningPortfolio.positions.extend(samplePositions)

            print 'New (Sample):'
            for position in samplePositions:
                date = filenameToday[filenameToday.find(fileMarketIndic) + len(fileMarketIndic):filenameToday.find('.txt')]
                openDate[position.symbol] = getStdStr(date)
                print position, openDate[position.symbol]

            #print 'Removed:'
            #for position in diffs.removedPositions:
            #    print position

            #print 'Running Portfolio:'
            #print runningPortfolio

            print len(runningPortfolio.positions)

        # Get historical prices and calculate P&L
        for position in runningPortfolio.positions:
            date = filename[filename.find(fileMarketIndic) + len(fileMarketIndic):
                            filename.find('.txt')]
            fromDate = getStdStr(date)
            #fromDate = openDate[position.symbol]
            fromYear = int(fromDate[0:4])
            fromMonth = int(fromDate[4:6])
            fromDay = int(fromDate[6:8])

            date = filenameToday[filenameToday.find(fileMarketIndic) + len(fileMarketIndic):
                                 filenameToday.find('.txt')]
            toDate = getStdStr(date)
            toYear = int(toDate[0:4])
            toMonth = int(toDate[4:6])
            toDay = int(toDate[6:8])

            prices = DataReader(position.symbol,  'yahoo',
                                datetime(fromYear, fromMonth, fromDay),
                                datetime(toYear, toMonth, toDay))
            print position.symbol + ',',
            for date in prices.index:
                print str(date.year) + '-' + str(date.month).zfill(2) + '-' + str(date.day).zfill(2) + ',',
            print
            print position.symbol + ',',
            for date in prices.index:
                dt = str(date.year) + str(date.month).zfill(2) + str(date.day).zfill(2)
                if dt < openDate[position.symbol]:
                    print ',',
                else:
                    print str(prices['Adj Close'][date]) + ',',
            print

        portfolioToday = readPortfolio(market, dateToday, source)
        print 'numPositions =', len(portfolioToday.positions)
