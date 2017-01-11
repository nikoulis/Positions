from xlrd import open_workbook
import time
import sys
import glob
import imaplib
import email
import os
import pdb
import pandas as pd
from datetime import datetime
from pandas.io.data import DataReader
from sectors import *
import util

#------------------------------------------------------------------
# Indicative stock information (name, sector, industry, market cap
#------------------------------------------------------------------
class StockInfo:
    def __init__(self, name='', sector='', industry='', marketCap=''):
        util.initFromArgs(self)
        self.marketCapNum = getMarketCapNum(marketCap)

    def __str__(self):
        return(self.name + '|' +
               self.sector + '|' +
               self.industry + '|' +
               self.marketCap + '|' +
               str(self.marketCapNum))

#-------------------------
# Trade performance class
#-------------------------
class Performance:
    def __init__(self,
                 market='US',
                 symbol='',
                 name = '',
                 sector = '',
                 direction='',
                 numShares=0,
                 entryDate=0,
                 exitDate=0,
                 entryPrice=0,
                 exitPrice=0,
                 entryAmount=0,
                 currentAmount=0,
                 retAmount=0,
                 ret=0):
        util.initFromArgs(self)

    def __str__(self):
        return '%-8s %-30s %-5s %5s %9s %9s %8.2f %8.2f %8.2f %8.2f %8.2f %7.2f%%' % (
            self.symbol[:self.symbol.find('_')],
            self.name,
            self.direction,
            self.numShares,
            getMatchStr(str(self.entryDate)),
            getMatchStr(str(self.exitDate)),
            self.entryPrice,
            self.exitPrice,
            self.entryAmount,
            self.currentAmount,
            self.retAmount,
            self.ret)

    def toTxt(self):
        return '%s|%s|%s|%s|%s|%s|%s|%f|%f|%f|%f|%f|%f' % (
            self.symbol[:self.symbol.find('_')],
            self.name,
            self.sector,
            self.direction,
            self.numShares,
            str(self.entryDate),
            str(self.exitDate),
            self.entryPrice,
            self.exitPrice,
            self.entryAmount,
            self.currentAmount,
            self.retAmount,
            self.ret)

    def readTxt(self, line):
        data = line.strip().split('|')
        self.symbol = data[0] + '_' + data[5]
        self.name = data[1]
        self.sector = data[2]
        self.direction = data[3]
        self.numShares = int(data[4])
        self.entryDate = int(data[5])
        self.exitDate = int(data[6]) if data[6] != '' else 0
        self.entryPrice = float(data[7])
        self.exitPrice = float(data[8])
        self.entryAmount = float(data[9])
        self.currentAmount = float(data[10])
        self.retAmount = float(data[11])
        self.ret = float(data[12])

#------------------------
# Portfolio return class
#------------------------
class PortfolioReturn:
    def __init__(self,
                 market='US',
                 date='',
                 totEntryAmount=0,
                 totCurrentAmount=0,
                 totRetAmount=0,
                 totRet=0):
        util.initFromArgs(self)

    def __str__(self):
        return '%10s %10.2f %10.2f %7.2f%%' % (
            self.date,
            self.totEntryAmount,
            self.totRetAmount,
            self.totRet)

    def toCsv(self):
        return '%s,%f,%f,%f,%f' % (
            self.date,
            self.totEntryAmount,
            self.totCurrentAmount,
            self.totRetAmount,
            self.totRet)

#--------------------------------------------------------
# A position is a symbol and a direction (Long or Short)
#--------------------------------------------------------
class Position:
    def __init__(self, direction, symbol, entryDate=0, exitDate=0):
        util.initFromArgs(self)

    def __str__(self):
        return(self.direction + ',' +
               self.symbol + ',' +
               str(self.entryDate) + ',' +
               str(self.exitDate))

    # To see if 'other' position is in portfolio, check if symbols (without _entryDate) are equal and if exitDate is zero
    def __eq__(self, other):
        return (self.direction == other.direction and
                self.symbol[:self.symbol.find('_')] == other.symbol[:other.symbol.find('_')] and
                self.exitDate ==  0)

#------------------------------------
# A portfolio is a list of positions
#------------------------------------
class Portfolio:
    def __init__(self, market):
        self.positions = []
        self.market = market

    def __str__(self):
        portfolioStr = ''
        for position in self.positions:
            portfolioStr += (position.direction + ' ' +
                             position.symbol + ' ' +
                             str(position.entryDate) + ' ' +
                             str(position.exitDate) + '\n')
        return portfolioStr

    #-------------------------------------------------------------
    # Read from csv file (Direction, Symbol, entryDate, exitDate)
    #-------------------------------------------------------------
    def readCsv(self, filename, direction='Long', entryDate=0, exitDate=0):
        self.positions = []
        f = open(filename)
        for line in f:
            data = line.strip().split(',')
            if len(data) == 1:
                symbol = data[0]
            else:
                if len(data) >= 2:
                    direction = data[0]
                    symbol = data[1]
                    if len(data) >= 3:
                        entryDate = int(data[2])
                        if len(data) >= 4:
                            exitDate = int(data[3])

            if symbol.find('_') > 0:
                symbolStr = symbol[:symbol.find('_')] + '_' + str(entryDate)
            else:
                symbolStr = symbol + '_0'
            position = Position(direction, symbolStr, entryDate, exitDate)
            self.positions.append(position)
        f.close()

    #------------------------------------------------------------
    # Write to csv file (Direction, Symbol, entryDate, exitDate)
    #------------------------------------------------------------
    def writeCsv(self, filename):
        f = open(filename, 'w')
        for position in self.positions:
            f.write(str(position) + '\n')
        f.close()

    #--------------------------------
    # Add positions to the portfolio
    #--------------------------------
    def addPositions(self, positions):
        self.positions.extend(positions)

    #---------------------------------
    # Remove positions from portfolio
    #---------------------------------
    def removePositions(self, positions):
        for position in positions:
            self.positions.pop(position)

    #----------------------
    # Read from Excel file
    #----------------------
    def readExcel(self, filename):
        self.positions = []
        wb = open_workbook(filename)
        for sheet in wb.sheets():
            number_of_rows = sheet.nrows
            number_of_columns = sheet.ncols
            rows = []
            for row in range(0, number_of_rows):
                values = []
                for col in range(number_of_columns):
                    value  = sheet.cell(row, col).value
                    try:
                        value.replace(' ', '')
                    except ValueError:
                        pass
                    finally:
                        values.append(value)
                position = Position(*values)
                self.positions.append(position)

    #-----------------------------------------------------------------
    # Read US stocks from text file (as saved in Outlook) -- OBSOLETE
    #-----------------------------------------------------------------
    def readOutlookUS(self, filename):
        longString = 'LONG'
        shortString = 'SHORT'
        f = open(filename, 'rb')
        foundLong = False
        foundShort = False
        for line in f:
            strings = line.strip().split()
            if (strings != [] and strings[0] == longString) or foundLong:
                foundLong = True
                foundShort = False
                if strings != []:
                    if strings[0] == longString:
                        values = ['Long', strings[1]]
                        #print values
                    elif strings[0] != shortString:
                        values = ['Long', strings[0]]
                        #print values
            if (strings != [] and strings[0] == shortString) or foundShort:
                foundShort = True
                foundLong = False
                if strings != []:
                    if strings[0] == shortString:
                        symbol = strings[1]
                    else:
                        symbol = strings[0]
                    values = ['Short', symbol]
                    #print values
            if strings == [] or strings[0] == '':
                foundShort = False
                foundLong = False

            if foundShort or foundLong:
                position = Position(*values)
                self.positions.append(position)
        f.close()

    #------------------------------------------------------------------
    # Read LSE stocks from text file (as saved in Outlook) -- OBSOLETE
    #------------------------------------------------------------------
    def readOutlookLSE(self, filename):
        longString = 'LONGS'
        shortString = 'SHORTS'
        f = open(filename, 'rb')
        foundLong = False
        foundShort = False
        for line in f:
            strings = line.strip().split()
            if (strings != [] and strings[0] == longString) or foundLong:
                foundLong = True
                foundShort = False
                if strings != []:
                    if strings[0] == longString:
                        pass
                    elif strings[0] != shortString:
                        values = ['Long', strings[0]]
                        #print values
            if (strings != [] and strings[0] == shortString) or foundShort:
                foundShort = True
                foundLong = False
                if strings != []:
                    if strings[0] == shortString:
                        pass
                    else:
                        values = ['Short', strings[0]]
                        #print values
            if strings == [] or strings[0] == '':
                foundShort = False
                foundLong = False

            if (foundShort or foundLong) and strings != [] and strings[0] != longString and strings[0] != shortString:
                position = Position(*values)
                self.positions.append(position)
        f.close()

    #---------------------------------------------------------------
    # Read stocks from Yahoo mail given a subject (P/LSE dd-mmm-yy)
    #---------------------------------------------------------------
    def readMail(self, subject):
        connection = imaplib.IMAP4_SSL('imap.mail.yahoo.com')
        connection.login('pnikoulis', 'ai024709th3669')
        connection.select(readonly=True)
        typ, data = connection.search(None, 'SUBJECT', subject)
        ids = data[0].split()
        id = ids[0]
        typ, data = connection.fetch(id, '(RFC822)')
        message = email.message_from_string(data[0][1])
        print '------------------------------------------> Message', id
        print 'Date:', message['Date']
        print 'From:', message['From']
        print 'Subject:', message['Subject']
        self.positions = getPositionsFromMessage(message)

    #------------------------------------------------------------------------
    # Check if a position is in portfolio (by checking symbol and exit date)
    #------------------------------------------------------------------------
    def inPositions(self, samplePosition):
        sampleSymbol = samplePosition.symbol[:samplePosition.symbol.find('_')]
        for position in self.positions:
            symbol = position.symbol[:position.symbol.find('_')]
            if (samplePosition.symbol == position.symbol or sampleSymbol == symbol) and position.exitDate == 0:
                return True
        return False
    
    #------------------------------------------------------------------------
    # Update portfolio based on diffs or a sample portfolio for a given date
    #------------------------------------------------------------------------
    def update(self, asofDate, asofPrevDate, display=False):
        # Read diffs file
        positionsNew, positionsRemoved = readDiffs(self.market + '-diffs-' + str(asofDate) + '.csv')

        # Also read benchmark portfolio for this date
        portfolioBenchmark = Portfolio(self.market)
        portfolioBenchmark = readPortfolio(self.market, asofDate, 'Yahoo')

        # Positions actually selected to be added to or removed from portfolio
        positionsNewSelected = []
        positionsRemovedSelected = []

        SAMPLE = True
        if SAMPLE:
            # Add a number of positions from the sample file (created by create-sample.py)
            samplePortfolio = Portfolio(self.market)
            samplePortfolio.readCsv(self.market + '-sample.csv')
            stockInfoHash = readSectorFile(self.market)
            if self.market == 'US-tradehero' or self.market == 'LSE-tradehero':
                NUM_DAILY_POSITIONS = 1
            else:
                NUM_DAILY_POSITIONS = 1

            numSamplePositions = min(len(samplePortfolio.positions), NUM_DAILY_POSITIONS)
            if numSamplePositions > 0:
                j = 0
                positionIndex = 0
                while j < numSamplePositions and positionIndex < len(samplePortfolio.positions):
                    samplePosition = samplePortfolio.positions[positionIndex]
                    print samplePosition
                    cutoffDate = 20151014
                    # If on or before cutoffDate, only check positionsRemoved (to be consistent
                    # with picks up to now); after cutoffDate, check benchmark portfolio instead
                    if ((asofDate <= cutoffDate and
                         (not self.inPositions(samplePosition)) and
                         (not samplePosition in positionsRemoved)) or
                        (asofDate > cutoffDate and
                         (not self.inPositions(samplePosition)) and
                         (samplePosition in portfolioBenchmark.positions))):
                        samplePosition.symbol = samplePosition.symbol[:samplePosition.symbol.find('_')] + '_' + str(asofDate)
                        samplePosition.entryDate = asofDate
                        self.positions.append(samplePosition)
                        positionsNewSelected.append(samplePosition)
                        j += 1
                    positionIndex += 1
                    
                if asofDate == 20160225: # and samplePosition.symbol[:5] == 'LXB.L':
                    pdb.set_trace()

                #---------------------------------------------------------------------------------
                # If we reached our limit, remove a number of positions to make room for new ones
                #---------------------------------------------------------------------------------
                MAX_POSITIONS = 100
                openPositions = [p for p in self.positions if p.exitDate == 0]
                if len(openPositions) > MAX_POSITIONS:
                    # 1. Read raw performance file and sort by group (sector+direction)
                    performances = readPerformances(self.market + '-rawperf-' + str(asofPrevDate) + '.txt')
                    groups = {}
                    for performance in [p for p in performances if p.exitDate == 0]:
                        k = performance.sector + '-' + performance.direction
                        if groups.get(k) is None:
                            groups[k] = []
                        groups[k].append((performance.symbol, performance.ret))
                    for k in groups.keys():
                        groups[k] = sorted(groups[k], key=lambda t: t[1])

                    # 2. Remove positions from the same group as ones added (picking worst performing ones first)
                    posId = 0
                    for position in positionsNewSelected:
                        k = stockInfoHash[position.symbol[:position.symbol.find('_')]].sector + '-' + position.direction
                        try:
                            position = [p for p in self.positions if p.symbol == groups[k][posId][0] and p.exitDate == 0][0]
                        except IndexError:
                            pass
                        positionsRemoved.append(position)
                        posId += 1

                self.writeCsv(self.market + '-portfolio.csv')
        else:
            # Add all new positions to global portfolio, if not already there
            f = open(self.market + '-portfolio.csv', 'a')
            for p in positionsNew:
                p.entryDate = asofDate
                if p in self.positions:
                    print 'Skipping', str(p)
                else:
                    print 'Adding', str(p)
                    f.write(str(p) + '\n')
                    # Also update sectors file
                    s = open('allsectors.txt', 'a')
                    name, sector, industry, marketCap = getYahooFinanceData(p.symbol[:p.symbol.find('_')])
                    marketCapNum = getMarketCapNum(marketCap)
                    print p.symbol, name, sector, industry, marketCap, marketCapNum
                    s.write(p.symbol[:p.symbol.find('_')] + ',' + sector + ',' + str(marketCapNum) + '\n')
                    s.close()
            f.close()

        # Set exit date for removed positions
        self.readCsv(self.market + '-portfolio.csv')
        newPortfolio = Portfolio(self.market)
        for position in self.positions:
            positionSymbol = position.symbol[:position.symbol.find('_')]
            removedSymbols = [p.symbol for p in positionsRemoved]
            if position in positionsRemoved or (positionSymbol in removedSymbols and position.exitDate == 0):
                position.exitDate = asofDate
                print 'Set exitDate of', str(position)
                positionsRemovedSelected.append(position)
            newPortfolio.positions.append(position)
        newPortfolio.writeCsv(self.market + '-portfolio.csv')
        newPortfolio.writeCsv(self.market + '-portfolio-' + str(asofDate) + '.csv')
        writeDiffs(positionsNewSelected, positionsRemovedSelected, self.market + '-new-removed-' + str(asofDate) + '.csv')
        if display:
            self.showStats(stockInfoHash)

    #----------------------------------
    # Download prices from Yahoo Finance
    #----------------------------------
    def downloadPrices(self, startDate, endDate):
        pricesOpenFilename = 'open-prices-' + self.market + '.csv'
        pricesAdjCloseFilename = 'adjclose-prices-' + self.market + '.csv'
        pricesCloseFilename = 'close-prices-' + self.market + '.csv'

        i = 0
        for position in self.positions:
            symbol = position.symbol[:position.symbol.find('_')]
            try:
                allData = DataReader(normalizeSymbol(symbol), 'yahoo', datetime(2015, 4, 22), endDate)
            except IOError:
                pass
            print allData.tail(10)

            # Get open prices
            tsOpen = allData['Open']
            dataOpen = pd.DataFrame(list(tsOpen.values), index=tsOpen.index, columns=[symbol])
            if i == 0:
                pricesOpen = dataOpen
            else:
                pricesOpen = pd.concat([pricesOpen, dataOpen], axis=1)
            pricesOpen = pricesOpen.fillna(method='pad')
            print pricesOpen.tail(10)

            # Get adjusted close prices
            tsAdjClose = allData['Adj Close']
            dataAdjClose = pd.DataFrame(list(tsAdjClose.values), index=tsAdjClose.index, columns=[symbol])
            if i == 0:
                pricesAdjClose = dataAdjClose
            else:
                pricesAdjClose = pd.concat([pricesAdjClose, dataAdjClose], axis=1)
            pricesAdjClose = pricesAdjClose.fillna(method='pad')
            print pricesAdjClose.tail(10)

            # Get unadjusted close prices
            tsClose = allData['Close']
            dataClose = pd.DataFrame(list(tsClose.values), index=tsClose.index, columns=[symbol])
            if i == 0:
                pricesClose = dataClose
            else:
                pricesClose = pd.concat([pricesClose, dataClose], axis=1)
            pricesClose = pricesClose.fillna(method='pad')
            print pricesClose.tail(10)

            i += 1

        # Store only data after startDate
        startIndex = pricesOpen.index.searchsorted(startDate)
        pricesOpen = pricesOpen.ix[startIndex:]
        pricesOpen.to_csv(pricesOpenFilename)
        pricesAdjClose = pricesAdjClose.ix[startIndex:]
        pricesAdjClose.to_csv(pricesAdjCloseFilename)
        pricesClose = pricesClose.ix[startIndex:]
        pricesClose.to_csv(pricesCloseFilename)

    #---------------------------------
    # Calculate portfolio performance
    #---------------------------------
    def calcPerformance(self, asofDate, verbose=False):
        # Read data from file
        pricesOpenFilename = 'open-prices-' + self.market + '.csv'
        pricesAdjCloseFilename = 'adjclose-prices-' + self.market + '.csv'
        pricesCloseFilename = 'close-prices-' + self.market + '.csv'

        pricesOpen = readPricesFromFile(pricesOpenFilename)
        pricesAdjClose = readPricesFromFile(pricesAdjCloseFilename)
        pricesClose = readPricesFromFile(pricesCloseFilename)

        currentDate = int(time.strftime('%Y%m%d'))
        POSITION_SIZE = 1000
        MARGIN = 0.5   # i.e. 50% margin must be put up for short sales
        totEntryAmount = 0
        totCurrentAmount = 0
        totRetAmount = 0
        performances = []
        if verbose:
            print '-----------------------------------------------------------------------------------------------------------------------------'
            print 'Portfolio                               Dir   #Shrs  Entry Dt   Exit Dt Entry Px  Exit Px  Entry $   Exit $      P&L   Return'
            print '-----------------------------------------------------------------------------------------------------------------------------'

        stockInfoHash = readSectorFile(self.market)
        for position in [p for p in self.positions if p.entryDate <= asofDate]:
            symbol = position.symbol[:position.symbol.find('_')]

            #if symbol == 'UNM' and asofDate == 20151231:
            #    pdb.set_trace()

            # Get exit price; adjust based on this day's closing price (closing prices
            # are adjusted in the Yahoo data, but open, high and low prices are not!)
            lastDate = datetime(*getDateComponents(str(asofDate)))
            lastDateIndex = min(len(pricesAdjClose) - 1, pricesAdjClose.index.searchsorted(lastDate))
            exitPrice = pricesAdjClose.ix[lastDateIndex][symbol]
            if position.exitDate > 0:
                exitDate = datetime(*getDateComponents(str(position.exitDate)))
                nextExitDateIndex = pricesAdjClose.index.searchsorted(exitDate) + 1
                if nextExitDateIndex <= lastDateIndex:
                    # Position has exited prior to lastDate; can use next open for exit price
                    # (otherwise, lastDate's adjusted close price is used)
                    adjustmentFactor = pricesAdjClose.ix[nextExitDateIndex][symbol] / pricesClose.ix[nextExitDateIndex][symbol]
                    exitPrice = pricesOpen.ix[nextExitDateIndex][symbol] * adjustmentFactor

            # Get entry price; also adjust based on this day's closing price (closing prices
            # are adjusted in the Yahoo data, but open, high and low prices are not!)
            entryDate = datetime(*getDateComponents(str(position.entryDate)))
            nextOpenDateIndex = pricesOpen.index.searchsorted(entryDate) + 1
            if nextOpenDateIndex > lastDateIndex:
                # Force zero return for last date's positions
                entryPrice = exitPrice
            else:
                adjustmentFactor = pricesAdjClose.ix[nextOpenDateIndex][symbol] / pricesClose.ix[nextOpenDateIndex][symbol]
                entryPrice = pricesOpen.ix[nextOpenDateIndex][symbol] * adjustmentFactor

            # For below calcs, see also lsepx.xlsx
            if position.direction == 'Short':
                #print symbol, entryPrice
                # Hardcoding AV's entry price (for some reason, prices prior to 3-Dec-2015 disappeared on Yahoo Finance -- as of 31-Dec-2015)
                if symbol == 'AV':
                    entryPrice = 14.79
                numShares = max(1, int(float(POSITION_SIZE) / float(entryPrice) / MARGIN))
                multiplier = MARGIN
                direction = -1.0
            else:
                numShares = max(1, int(float(POSITION_SIZE) / float(entryPrice)))
                multiplier = 1.0
                direction = 1.0
            entryAmount = numShares * entryPrice * multiplier
            currentAmount = numShares * exitPrice * multiplier
            retAmount = (currentAmount - entryAmount) * direction / multiplier
            ret = 100.0 * retAmount / entryAmount
            """
            maxDates = len(pricesAdjClose.index)
            if position.entryDate == 0:
                entryDate = ''
            else:
                entryDateTimestamp = datetime(*getDateComponents(str(position.entryDate)))
                nextEntryDateIndex = pricesAdjClose.index.searchsorted(entryDateTimestamp) + 1
                if nextEntryDateIndex < maxDates:
                    entryDate = int(str(pricesAdjClose.index[nextEntryDateIndex])[:10].replace('-', ''))
                else:
                    entryDate = currentDate
            if position.exitDate == 0:
                exitDate = ''
            else:
                exitDateTimestamp = datetime(*getDateComponents(str(position.exitDate)))
                nextExitDateIndex = pricesAdjClose.index.searchsorted(exitDateTimestamp) + 1
                if nextExitDateIndex < maxDates:
                    exitDate = int(str(pricesAdjClose.index[nextExitDateIndex])[:10].replace('-', ''))
                else:
                    exitDate = currentDate
            """
            if position.entryDate == 0:
                entryDate = ''
            else:
                entryDate = position.entryDate
            if position.exitDate == 0:
                exitDate = ''
            else:
                exitDate = position.exitDate
            performance = Performance(self.market,
                                      position.symbol,
                                      stockInfoHash[symbol].name[:30],
                                      stockInfoHash[symbol].sector,
                                      position.direction,
                                      numShares,
                                      entryDate,
                                      exitDate,
                                      entryPrice,
                                      exitPrice,
                                      entryAmount,
                                      currentAmount,
                                      retAmount,
                                      ret)
            performances.append(performance)
            if verbose:
                print str(performance)

            totEntryAmount += entryAmount
            totCurrentAmount += currentAmount
            totRetAmount += retAmount
            totRet = 100.0 * totRetAmount / totEntryAmount

        return totEntryAmount, totCurrentAmount, totRetAmount, totRet, performances

    #---------------------------
    # Show portfolio statistics
    #---------------------------
    def showStats(self, stockInfoHash):
        sectorPositions, sectorPercent = calcSectorPercent(self, stockInfoHash)

        print('----------------------------------------------')
        print '              Sector:  Nlng Nshrt  Plng  Pshrt'
        print('----------------------------------------------')
        for sectorName in sectorPositions.keys():
            print ('%20s: %5.0f %5.0f %5.1f %5.1f') % (sectorName,
                                                       len(sectorPositions[sectorName]['Long']),
                                                       len(sectorPositions[sectorName]['Short']),
                                                       sectorPercent[sectorName]['Long'],
                                                       sectorPercent[sectorName]['Short'])
        print('----------------------------------------------')
        totalLong = len([p for p in self.positions if p.direction == 'Long' and p.exitDate == 0])
        totalShort = len([p for p in self.positions if p.direction == 'Short' and p.exitDate == 0])
        total = totalLong + totalShort
        if total == 0:
            pctLong = 0
            pctShort = 0
        else:
            pctLong = 100.0 * float(totalLong) / float(total)
            pctShort = 100.0 * float(totalShort) / float(total)
        print ('%20s: %5.0f %5.0f %5.1f %5.1f') % ('Total', totalLong, totalShort, pctLong, pctShort)
        print('----------------------------------------------')

#-----------------------
# Read prices from file
#-----------------------
def readPricesFromFile(filename):
    prices = pd.read_csv(filename)
    prices = prices.fillna(method='pad')
    dateColumn = prices.columns[0]
    prices = prices.set_index(dateColumn)
    prices.index = prices.index.to_datetime()
    return prices

#-------------------------------------------------------------------------------------------
# Determine positions from a list of strings (e.g. 'LONG', 'AAPL', 'MSFT', 'SHORT', 'GOOG')
#-------------------------------------------------------------------------------------------
def getPositionsFromStrings(strings):
    positions = []
    foundLong = False
    foundShort = False
    for string in strings:
        if string == 'LONGS' or string == 'LONG':
            foundLong = True
            foundShort = False
        elif foundLong and string != 'SHORT' and string != 'SHORTS':
            # Don't include SHORT (or SHORTS) as a symbol
            values = ['Long', string]
            position = Position(*values)
            positions.append(position)
        elif string == 'SHORTS' or string == 'SHORT':
            foundShort = True
            foundLong = False
        elif foundShort:
            # Assumes shorts come after longs
            values = ['Short', string]
            position = Position(*values)
            positions.append(position)
    return positions

#--------------------------------------------------
# Read new and removed positions from a diffs file
#--------------------------------------------------
def readDiffs(filename):
    f = open(filename)
    positionsNew = []
    positionsRemoved = []
    for line in f:
        data = line.strip().split(',')
        action = data[0]
        direction = data[1]
        symbol = data[2]
        position = Position(direction, symbol)
        if action == 'New':
            positionsNew.append(position)
        else:
            positionsRemoved.append(position)
    return positionsNew, positionsRemoved

#-------------------------------------------------
# Write new and removed positions to a diffs file
#-------------------------------------------------
def writeDiffs(positionsNew, positionsRemoved, filename):
    f = open(filename, 'w')
    for position in positionsNew:
        f.write('New,' + position.direction + ',' + position.symbol + '\n')
    for position in positionsRemoved:
        f.write('Removed,' + position.direction + ',' + position.symbol + '\n')
    f.close()

#----------------------------------------------------------------------------------
# Find differences between two portfolios (i.e. new positions and closed positions
#----------------------------------------------------------------------------------
class Diffs:
    def __init__(self, portfolio1, portfolio2):
        positions1 = portfolio1.positions
        positions2 = portfolio2.positions
        self.newPositions = [position for position in positions2 if position not in positions1]
        self.removedPositions = [position for position in positions1 if position not in positions2]
        self.remainingPositions = [position for position in positions1 if position in positions2]

#-----------------------------------
# Read a portfolio given a filename
#-----------------------------------
def readPortfolio(market, date, source):
    portfolio = Portfolio(market)
    if source == 'Excel':
        # Read from Excel
        portfolio.readExcel(date + '.xlsx')
    elif source == 'Outlook':
        # Read from Outlook mail message (which has been saved automatically)
        if getMarket(market) == 'US':
            filename = glob.glob('c:/mails/*_ ' + 'P ' + getMatchStr(str(date)) + '.txt')[0]
            portfolio.readOutlookUS(filename)
        else:
            filename = glob.glob('c:/mails/*_ ' + 'LSE ' + getMatchStr(str(date)) + '.txt')[0]
            portfolio.readOutlookLSE(filename)
    elif source == 'Yahoo':
        # Read from Yahoo mail (or from text file, if it exists)
        filename = getMarket(market) + '-' + str(date) + '.csv'
        if os.path.exists(filename):
            portfolio.readCsv(filename)
        else:
            if getMarket(market) == 'US':
                subject = 'P ' + getMatchStr(str(date))
            else:
                subject = 'LSE ' + getMatchStr(str(date))
            portfolio.readMail(subject)
            #f = open(filename, 'w')
            #for position in portfolio.positions:
            #    f.write(str(position) + '\n')
            #f.close()

    return portfolio

#------------------------------------------
# Read a performance file given a filename
#------------------------------------------
def readPerformances(filename):
    performances = []
    f = open(filename)
    for line in f:
        performance = Performance()
        performance.readTxt(line)
        performances.append(performance)
    return performances

#-------------------------------------------------------------------------------------------
# Return year, month and day given a standard date (e.g. for 20150710, return (2015, 7, 10)
#-------------------------------------------------------------------------------------------
def getDateComponents(stdStr):
    year = int(stdStr[0:4])
    month = int(stdStr[4:6])
    day = int(stdStr[6:8])
    monthName = time.strftime('%b', (year, month, day, 0, 0, 0, 0, 0, 0))
    return year, month, day

#-----------------------------------------------------------------------------------------
# Return correct match string given a standard date (e.g. for 20150710, return 10-Jul-15)
#-----------------------------------------------------------------------------------------
def getMatchStr(stdStr, showFullYear=False):
    if stdStr == '':
        return ''
    else:
        year = int(stdStr[0:4])
        month = int(stdStr[4:6])
        day = int(stdStr[6:8])
        monthName = time.strftime('%b', (year, month, day, 0, 0, 0, 0, 0, 0))
        yearStart = 0 if showFullYear else 2
        return str(day) + '-' + monthName + '-' + stdStr[yearStart:4]

#-------------------------------------------------------------------------------
# Return standard date given a match date (e.g. for 10-Jul-15, return 20150710)
#-------------------------------------------------------------------------------
def getStdStr(matchStr):
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    day = matchStr[:matchStr.index('-')].zfill(2)
    monthName = (matchStr[matchStr.index('-') + 1:matchStr.index('-', 3)]).lower().capitalize()
    month = str(months.index(monthName) + 1).zfill(2)
    year = '20' + matchStr[matchStr.index('-', 3) + 1:]
    return year + month + day

#---------------------------------
# Get the list of dates from file
#---------------------------------
def getDates(market):
    dates = []
    f = open(getMarket(market) + '-dates.csv')
    for line in f:
        data = line.strip()
        dates.append(int(data))
    return dates

#---------------------------------------------------
# Get the list of dates from Yahoo and save in file
#---------------------------------------------------
def updateDates(market):
    # Read dates from file
    dates = []
    try:
        f = open(getMarket(market) + '-dates.csv')
        for line in f:
            data = line.strip()
            dates.append(data)
        f.close()
        if len(dates) > 0:
            lastDate = dates[-1]
        else:
            lastDate = 0
    except:
        lastDate = 0

    if getMarket(market) == 'US':
        fileMarketIndic = 'P '
    else:
        fileMarketIndic = 'LSE '

    # Read emails and keep a newDates list in order to update dates file
    connection = imaplib.IMAP4_SSL('imap.mail.yahoo.com')
    connection.login('pnikoulis', 'ai024709th3669')
    connection.select(readonly=True)
    typ, data = connection.search(None, 'ALL')
    ids = data[0].split()
    numIds = len(ids)
    newDates = []
    for i in range(numIds - 1, -1, -1):
        id = ids[i]
        typ, data = connection.fetch(id, '(RFC822)')
        message = email.message_from_string(data[0][1])
        subject = message['Subject']

        # These are all emails that contain portfolio data (including replies and forwards)
        try:
            foundIndic = subject.find(fileMarketIndic)
        except:
            foundIndic = 0
        # These are alll emails that contain portfolio data (original, no replies or forwards)
        if foundIndic == 0:
            print '------------------------------------------> Message', id
            print 'Date:', message['Date']
            print 'From:', message['From']
            print 'Subject:', message['Subject']
            date = getStdStr(subject[len(fileMarketIndic):])
            if date <= lastDate:
                break
            newDates.append(date)
            filename = market + '-' + str(date) + '.csv'
            if (not os.path.exists(filename)) or os.stat(filename).st_size == 0:
                print 'Saving', filename
                benchmarkPortfolio = Portfolio(market)
                benchmarkPortfolio.positions = getPositionsFromMessage(message)
                benchmarkPortfolio.writeCsv(filename)

    # Update dates file
    newDates = sorted(newDates)
    f = open(getMarket(market) + '-dates.csv', 'a')
    for date in newDates:
        f.write(str(date) + '\n')
    f.close()
    dates = getDates(market)
    return dates

#-------------------------------------------------
# Parse a message body and return positions array
#-------------------------------------------------
def getPositionsFromMessage(message):
    payload = message.get_payload()
    while isinstance(payload[0], email.message.Message):
        payload = payload[0].get_payload()
    payload = payload.replace('=\r\n', '')
    strings = payload.split()
    positions = getPositionsFromStrings(strings)
    return positions

#---------------------------------------
# Get market from market-version string
#---------------------------------------
def getMarket(market):
    if '-' in market:
        return market[:market.index('-')]
    else:
        return market

#------------------
# Read sector file
#------------------
def readSectorFile(market):
    filename = 'sectors-' + getMarket(market) + '.txt'
    f = open(filename)
    stockInfoHash = {}
    for line in f:
        data = line.strip().split('|')
        stockInfo = StockInfo(*(data[1:5]))
        stockInfoHash[data[0]] = stockInfo
    return stockInfoHash

#-------------------
# Write sector file
#-------------------
def writeSectorFile(market, stockInfoHash):
    # Read sector file
    currentStockInfoHash = readSectorFile(market)
    currentSymbols = currentStockInfoHash.keys()

    # Add stocks that are not in current sector file
    filename = 'sectors-' + getMarket(market) + '.txt'
    f = open(filename, 'a')
    for symbol in stockInfoHash.keys():
        if symbol not in currentSymbols:
            f.write(symbol + '|' + str(stockInfoHash(symbol)))
    f.close()

#-------------------------------------------------------------------------------------------------
# Calculate percentage of stocks for each sector in a portfolio; also return positions per sector
#-------------------------------------------------------------------------------------------------
def calcSectorPercent(portfolio, stockInfoHash):
    sectorNames = ['Basic Materials',
                   'Conglomerates',
                   'Consumer Goods',
                   'Financial',
                   'Healthcare',
                   'Industrial Goods',
                   'Services',
                   'Technology',
                   'Utilities',
                   'Currency ETF',
                   'Global ETF']
    directions = ['Long',
                  'Short']

    sectorPositions = {}
    sectorPercent = {}
    for sectorName in sectorNames:
        sectorPositions[sectorName] = {}
        sectorPercent[sectorName] = {}
        for direction in ('Long', 'Short'):
            sectorPositions[sectorName][direction] = []
            sectorPercent[sectorName][direction] = 0

    openPositions = [p for p in portfolio.positions if p.exitDate == 0]
    for position in openPositions:
        if (stockInfoHash.get(position.symbol[:position.symbol.find('_')]) != None and
            stockInfoHash.get(position.symbol[:position.symbol.find('_')]).sector != None and
            stockInfoHash.get(position.symbol[:position.symbol.find('_')]).sector != ''):
            sectorName = stockInfoHash[position.symbol[:position.symbol.find('_')]].sector
            sectorPositions[sectorName][position.direction].append(position)

    numPositions = sum([len(sectorPositions[sectorName][direction])
                        for sectorName in sectorNames
                        for direction in directions])
    for sectorName in sectorNames:
        for direction in sectorPositions[sectorName]:
            numSectorPositions = len(sectorPositions[sectorName][direction])
            if numSectorPositions == 0:
                sectorPercent[sectorName][direction] = 0
            else:
                sectorPercent[sectorName][direction] = 100.0 * float(numSectorPositions) / float(numPositions)

    print 'Num stocks with identified sectors: %d out of %d' % (numPositions, len(openPositions))
    return sectorPositions, sectorPercent

#--------------------------------------------------------
# Given two dates, determine diffs and save them in file
#--------------------------------------------------------
def calcDiffs(market, dateYesterday, dateToday, SOURCE, display=False):
    portfolioYesterday = readPortfolio(market, dateYesterday, SOURCE)
    portfolioToday = readPortfolio(market, dateToday, SOURCE)
    diffs = Diffs(portfolioYesterday, portfolioToday)

    f = open(market + '-diffs-' + str(dateToday) + '.csv', 'w')

    if display:
        print
        print 'Diffs between', dateYesterday, 'and', dateToday
        print '------------------------------------'
        print 'New:'
    for position in diffs.newPositions:
        if display:
            print position
        f.write('New,' + position.direction + ',' + position.symbol + '\n')

    if display:
        print 'Removed:'
    for position in diffs.removedPositions:
        if display:
            print position
        f.write('Removed,' + position.direction + ',' + position.symbol + '\n')

    f.close()

#------------------------------------------------
# Read two portfolios and find their differences
#------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: diffs.py <US/LSE> <yyyymmdd1> <yyyymmdd2>'
        sys.exit()

    # Only the Yahoo and Outlook sources support searching for the last two dates
    SOURCE = 'Yahoo'
    market = sys.argv[1]
    if getMarket(market) == 'US':
        fileMarketIndic = 'P '
    else:
        fileMarketIndic = 'LSE '

    if len(sys.argv) >= 4:
        # Use specified dates to determine filenames
        dateYesterday = sys.argv[2]
        dateToday = sys.argv[3]
    else:
        if SOURCE == 'Outlook':
            # Use the two latest filenames (based on time created) for this market
            filenameList = sorted(glob.glob('c:/mails/*_ ' + fileMarketIndic + '*.txt'))
            numFiles = len(filenameList)
            filenameYesterday = filenameList[numFiles - 2]
            filenameToday = filenameList[numFiles - 1]
            dateYesterday = getStdStr(filenameYesterday[filenameYesterday.find('_ ' + fileMarketIndic) + len(fileMarketIndic) + 2:
                                                        filenameYesterday.find('.txt')])
            dateToday = getStdStr(filenameToday[filenameToday.find('_ ' + fileMarketIndic) + len(fileMarketIndic) + 2:
                                                filenameToday.find('.txt')])
        elif SOURCE == 'Yahoo':
            dates = updateDates(market)
            #dates = getDates(market)
            dateToday = dates[-1]
            dateYesterday = dates[-2]

    calcDiffs(market, dateYesterday, dateToday, SOURCE)

    #=========================================================================#
    # Intervene here manually to the diffs file if needed, then run update.py #
    #=========================================================================#
