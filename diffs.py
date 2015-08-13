from xlrd import open_workbook
import time
import sys
import glob
import imaplib
import email
import os
import pdb

#--------------------------------------------------------
# A position is a symbol and a direction (Long or Short)
#--------------------------------------------------------
class Position:
    def __init__(self, direction, symbol, entryDate=0, exitDate=0):
        self.direction = direction
        self.symbol = symbol
        self.entryDate = entryDate
        self.exitDate = exitDate

    def __str__(self):
        return(self.direction + ',' + 
               self.symbol + ',' +
               str(self.entryDate) + ',' +
               str(self.exitDate))

    def __eq__(self, other):
        return ((self.direction == other.direction) and 
                (self.symbol == other.symbol))

#------------------------------------
# A portfolio is a list of positions
#------------------------------------
class Portfolio:
    def __init__(self):
        self.positions = []

    def __str__(self):
        portfolioStr = ''
        for position in self.positions:
            portfolioStr += (position.direction + ' ' +
                             position.symbol + ' ' +
                             str(position.entryDate) + ' ' +
                             str(position.exitDate) + '\n')
        return portfolioStr

    # Read from csv file (Direction, Symbol, entryDate, exitDate)
    def readCsv(self, filename):
        self.positions = []
        f = open(filename)
        for line in f:
            data = line.strip().split(',')
            position = Position(data[0], data[1], int(data[2]), int(data[3]))
            self.positions.append(position)
        f.close()

    # Write to csv file (Direction, Symbol, entryDate, exitDate)
    def writeCsv(self, filename):
        f = open(filename, 'w')
        for position in self.positions:
            f.write(str(position) + '\n')
        f.close()

    # Add positions to the portfolio
    def addPositions(self, positions):
        self.positions.extend(positions)
            
    # Remove positions from portfolio
    def removePositions(self, positions):
        for position in positions:
            self.positions.pop(position)

    # Read from Excel file
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

    # Read US stocks from text file (as saved in Outlook)
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

    # Read LSE stocks from text file (as saved in Outlook)
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

    # Read stocks from Yahoo mail given a subject (P/LSE dd-mmm-yy)
    def readMail(self, subject):
        connection = imaplib.IMAP4_SSL('imap.mail.yahoo.com')
        connection.login('pnikoulis', 'AgiouNikolaou12')
        connection.select()
        typ, data = connection.search(None, 'SUBJECT', subject)
        ids = data[0].split()
        id = ids[0]
        typ, data = connection.fetch(id, '(RFC822)')
        message = email.message_from_string(data[0][1])
        print '------------------------------------------> Message', id
        print 'Date:', message['Date']
        print 'From:', message['From']
        print 'Subject:', message['Subject']
        payload = message.get_payload()
        while isinstance(payload[0], email.message.Message):
            payload = payload[0].get_payload()
        strings = payload.split()

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
                self.positions.append(position)
            elif string == 'SHORTS' or string == 'SHORT':
                foundShort = True
                foundLong = False
            elif foundShort:
                # Assumes shorts come after longs
                values = ['Short', string]
                position = Position(*values)
                self.positions.append(position)

    #------------------------------------------------------------------------
    # Update portfolio based on diffs or a sample portfolio for a given date
    #------------------------------------------------------------------------
    def update(self, asofDate):
        # Read diffs file
        positionsNew = readDiffs(market + '-new-' + asofDate + '.csv')
        f = open(market + '-new-' + asofDate + '.csv')
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

        SAMPLE = True
        if SAMPLE:
            # Add a number of positions from the sample file (created by create-sample.py)
            samplePortfolio = Portfolio()
            samplePortfolio.readCsv(market + '-sample.csv')
            sectors = readSectorFile()
            NUM_DAILY_POSITIONS = 2
            portfolio = Portfolio()
            portfolio.readCsv(market + '-portfolio.csv')
            numSamplePositions = min(len(samplePortfolio.positions), NUM_DAILY_POSITIONS)
            if numSamplePositions > 0:
                j = 0
                positionIndex = 0
                while j < numSamplePositions and positionIndex < len(samplePortfolio.positions):
                    samplePosition = samplePortfolio.positions[positionIndex]
                    if not samplePosition in portfolio.positions:
                        samplePosition.entryDate = asofDate
                        portfolio.positions.append(samplePosition)
                        #del samplePortfolio.positions[j]
                        j += 1
                    positionIndex += 1

                showStats(portfolio, sectors)
                samplePortfolio.writeCsv(market + '-sample.csv')
                portfolio.writeCsv(market + '-portfolio.csv')
        else:
            # Add all new positions to global portfolio, if not already there
            f = open(market + '-portfolio.csv', 'a')
            for p in positionsNew:
                p.entryDate = asofDate
                if p in portfolio.positions:
                    print 'Skipping', str(p)
                else:
                    print 'Adding', str(p)
                    f.write(str(p) + '\n')
                    # Also update sectors file
                    s = open('allsectors.txt', 'a')
                    name, sector, industry, marketCap = getYahooFinanceData(p.symbol)
                    marketCapNum = getMarketCapNum(marketCap)
                    print p.symbol, name, sector, industry, marketCap, marketCapNum
                    s.write(p.symbol + ',' + sector + ',' + str(marketCapNum) + '\n')
                    s.close()
            f.close()

        # Set exit date for removed positions
        portfolio = Portfolio()
        portfolio.readCsv(market + '-portfolio.csv')
        newPortfolio = Portfolio()
        for position in portfolio.positions:
            if position in positionsRemoved:
                position.exitDate = asofDate
                print 'Set exitDate of', str(position)
            newPortfolio.positions.append(position)
        newPortfolio.writeCsv(market + '-portfolio.csv')
        newPortfolio.writeCsv(market + '-portfolio-' + asofDate + '.csv')


#--------------------------------------------------
# Read new and removed positions from a diffs file
#--------------------------------------------------
def readDiffs(filename):
    f = open(market + '-new-' + asofDate + '.csv')
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
    return newPositions, removedPositions

#----------------------------------------------------------------------------------
# Find differences between two portfolios (i.e. new positions and closed positions
#----------------------------------------------------------------------------------
class Diffs:
    def __init__(self, portfolio1, portfolio2):
        positions1 = portfolio1.positions
        positions2 = portfolio2.positions
        self.newPositions = [position for position in positions2 if position not in positions1]
        self.removedPositions = [position for position in positions1 if position not in positions2]

#-----------------------------------
# Read a portfolio given a filename
#-----------------------------------
def readPortfolio(market, date, source):
    portfolio = Portfolio()
    if source == 'Excel':
        # Read from Excel
        portfolio.readExcel(date + '.xlsx')
    elif source == 'Outlook':
        # Read from Outlook mail message (which has been saved automatically)
        if market == 'US':
            filename = glob.glob('c:/mails/*_ ' + 'P ' + getMatchStr(date) + '.txt')[0]
            portfolio.readOutlookUS(filename)
        else:
            filename = glob.glob('c:/mails/*_ ' + 'LSE ' + getMatchStr(date) + '.txt')[0]
            portfolio.readOutlookLSE(filename)
    elif source == 'Yahoo':
        # Read from Yahoo mail (or from text file, if it exists)
        filename = market + '-' + date + '.csv'
        if os.path.exists(filename):
            portfolio.readCsv(filename)
        else:
            if market == 'US':
                subject = 'P ' + getMatchStr(date)
            else:
                subject = 'LSE ' + getMatchStr(date)
            portfolio.readMail(subject)
            f = open(filename, 'w')
            for position in portfolio.positions:
                f.write(str(position) + '\n')
            f.close()

    return portfolio
    
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
def getMatchStr(stdStr):
    year = int(stdStr[0:4])
    month = int(stdStr[4:6])
    day = int(stdStr[6:8])
    monthName = time.strftime('%b', (year, month, day, 0, 0, 0, 0, 0, 0))
    return str(day) + '-' + monthName + '-' + stdStr[2:4]

#---------------------------------------------------------------------------------
# Return standard date given a match date (e.g. for 10-Jul-2015, return 20150710)
#---------------------------------------------------------------------------------
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
    f = open(market + '-dates.csv')
    for line in f:
        data = line.strip()
        dates.append(data)
    return dates

#---------------------------------------------------
# Get the list of dates from Yahoo and save in file
#---------------------------------------------------
def updateDates(market):
    # Read dates from file
    dates = []
    try:
        f = open(market + '-dates.csv')
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

    if market == 'US':
        fileMarketIndic = 'P '
    else:
        fileMarketIndic = 'LSE '

    # Read emails and keep a newDates list in order to update dates file
    connection = imaplib.IMAP4_SSL('imap.mail.yahoo.com')
    connection.login('pnikoulis', 'AgiouNikolaou12')
    connection.select()
    typ, data = connection.search(None, 'FROM', 'nmitsiou@gmail.com')
    ids = data[0].split()
    numIds = len(ids)
    newDates = []
    for i in range(numIds - 1, -1, -1):
        id = ids[i]
        typ, data = connection.fetch(id, '(RFC822)')
        message = email.message_from_string(data[0][1])
        subject = message['Subject']
        # These are all emails that contain portfolio data (including replies and forwards)
        foundPortfolio = subject.find(fileMarketIndic)
        # These are alll emails that contain portfolio data (original, no replies or forwards)
        if foundPortfolio == 0:
            print '------------------------------------------> Message', id
            print 'Date:', message['Date']
            print 'From:', message['From']
            print 'Subject:', message['Subject']
            date = getStdStr(subject[len(fileMarketIndic):])
            if date <= lastDate:
                break
            newDates.append(date)

    # Update dates file
    newDates = sorted(newDates)
    f = open(market + '-dates.csv', 'a')
    for date in newDates:
        f.write(str(date) + '\n')
    f.close()
    dates = getDates(market)
    return dates

#------------------
# Read sector file
#------------------
def readSectorFile(filename='allsectors.csv'):
    f = open(filename)
    sectors = {}
    for line in f:
        data = line.strip().split(',')
        sectors[data[0]] = data[1]
    return sectors

#-------------------------------------------------------------------------------------------------
# Calculate percentage of stocks for each sector in a portfolio; also return positions per sector
#-------------------------------------------------------------------------------------------------
def calcSectorPercent(portfolio, sectors):
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

    for position in portfolio.positions:
        if sectors.get(position.symbol) != None and sectors.get(position.symbol) != '':
            sectorName = sectors[position.symbol]
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

    #print 'Num stocks with identified sectors: %d out of %d' % (numPositions, len(portfolio.positions))
    return sectorPositions, sectorPercent

#---------------------------
# Show portfolio statistics
#---------------------------
def showStats(portfolio, sectors):
    sectorPositions, sectorPercent = calcSectorPercent(portfolio, sectors)

    print('----------------------------------------------')
    for sectorName in sectorPositions.keys():
        print ('%20s: %5.0f %5.0f %5.1f %5.1f') % (sectorName,
                                                   len(sectorPositions[sectorName]['Long']),
                                                   len(sectorPositions[sectorName]['Short']),
                                                   sectorPercent[sectorName]['Long'],
                                                   sectorPercent[sectorName]['Short'])
    print('----------------------------------------------')
    totalLong = len([p for p in portfolio.positions if p.direction == 'Long'])
    totalShort = len([p for p in portfolio.positions if p.direction == 'Short'])
    total = totalLong + totalShort
    if total == 0:
        pctLong = 0
        pctShort = 0
    else:
        pctLong = 100.0 * float(totalLong) / float(total)
        pctShort = 100.0 * float(totalShort) / float(total)
    print ('%20s: %5.0f %5.0f %5.1f %5.1f') % ('Total', totalLong, totalShort, pctLong, pctShort)
    print('----------------------------------------------')

#--------------------------------------------------------
# Given two dates, determine diffs and save them in file
#--------------------------------------------------------
def saveDiffs(market, dateYesterday, dateToday, SOURCE):
    portfolioYesterday = readPortfolio(market, dateYesterday, SOURCE)
    portfolioToday = readPortfolio(market, dateToday, SOURCE)
    diffs = Diffs(portfolioYesterday, portfolioToday)

    f = open(market + '-diffs-' + dateToday + '.csv', 'w')

    print
    print 'Diffs between', dateYesterday, 'and', dateToday
    print '------------------------------------'
    print 'New:'
    for position in diffs.newPositions:
        print position
        f.write('New,' + position.direction + ',' + position.symbol + '\n')
    print

    print 'Removed:'
    for position in diffs.removedPositions:
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
    if market == 'US':
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

    saveDiffs(market, dateYesterday, dateToday, SOURCE)

    #=========================================================================#
    # Intervene here manually to the diffs file if needed, then run update.py #
    #=========================================================================#
