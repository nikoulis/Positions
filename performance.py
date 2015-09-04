import sys
sys.path.append('/home/nikoulis/anaconda/lib/python2.7/site-packages')  # For Ubuntu
from xlrd import open_workbook
from openpyxl import *
import urllib
import pandas as pd
from datetime import datetime
from time import strftime
import pdb
from diffs import *

#-----------------------------------------------------------------------------------
# Flatten a list of lists (used to calculate total number of trades, long or short)
#-----------------------------------------------------------------------------------
def flatten(l):
    return [item for sublist in l for item in sublist]

#---------------------------------
# Calculate portfolio performance
#---------------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: performance.py <US/LSE> <yyyymmmdd>'
        sys.exit()

    market = sys.argv[1]
    dates = getDates(market)
    if len(sys.argv) >= 3:
        asofDate = sys.argv[2]
    else:
        # Use last date from file
        asofDate = dates[-1]

    currentDate = int(time.strftime('%Y%m%d'))

    #asofDate = time.strftime('%Y%m%d')
    portfolio = Portfolio(market)
    portfolio.readCsv(market + '-portfolio.csv')

    # Download prices and calculate performance
    startDate = datetime(*getDateComponents(str(min([p.entryDate for p in portfolio.positions]))))
    endDate = datetime(*getDateComponents(str(asofDate)))
    DOWNLOAD = True
    if DOWNLOAD:
        portfolio.downloadPrices(startDate, endDate)
    FULL = False
    if FULL:
        startDateIndex = 0
    else:
        startDateIndex = dates.index(20150818)
    date = asofDate

    # From this point on, redirect output to file
    filename = market + '-perf-' + str(asofDate) + '.txt'
    sys.stdout = open(filename, 'w')

    totEntryAmount, totCurrentAmount, totRetAmount, totRet, performances = portfolio.calcPerformance(date, True)

    #-------------------------------------------------------------------------
    # Now present the trades in a different format (similar to the Excel file
    #-------------------------------------------------------------------------
    newTradePerformances = [[p for p in performances if p.entryDate == asofDate and
                             p.direction == 'Long'],
                            [p for p in performances if p.entryDate == asofDate and
                             p.direction == 'Short']]
    removedTradePerformances = [[p for p in performances if p.exitDate == asofDate and
                                 p.direction == 'Long'],
                                [p for p in performances if p.exitDate == asofDate and
                                 p.direction == 'Short']]
    openTradePerformances = [[p for p in performances if p.entryDate < asofDate and
                              (p.exitDate == '' or p.exitDate == asofDate) and p.direction == 'Long'],
                             [p for p in performances if p.entryDate < asofDate and
                              (p.exitDate == '' or p.exitDate == asofDate) and p.direction == 'Short']]
    closedTradePerformances = [[p for p in performances if p.entryDate < asofDate and p.exitDate != '' and
                                p.exitDate < asofDate and p.direction == 'Long'],
                               [p for p in performances if p.entryDate < asofDate and p.exitDate != '' and
                                p.exitDate < asofDate and p.direction == 'Short']]
    stockInfoHash = readSectorFile(market)

    print
    print '-----------------------------------------------------------------------------------------------------------------------------'
    print 'New Trades                              Dir   #Shrs  Entry Dt   Exit Dt Entry Px  Exit Px  Entry $   Exit $      P&L   Return'
    print '-----------------------------------------------------------------------------------------------------------------------------'
    numNewTrades = len(flatten(newTradePerformances))
    if numNewTrades == 0:
        print 'None'
    else:
        for newTrades in newTradePerformances:
            for p in newTrades:
                p.entryDate = currentDate
                print str(p)
    print
    print '-----------------------------------------------------------------------------------------------------------------------------'
    print 'Removed Trades                          Dir   #Shrs  Entry Dt   Exit Dt Entry Px  Exit Px  Entry $   Exit $      P&L   Return'
    print '-----------------------------------------------------------------------------------------------------------------------------'
    numRemovedTrades = len(flatten(removedTradePerformances))
    if numRemovedTrades == 0:
        print 'None'
    else:
        for removedTrades in removedTradePerformances:
            for p in removedTrades:
                p.exitDate = currentDate
                print str(p)
    print
    print '-----------------------------------------------------------------------------------------------------------------------------'
    print 'Open Trades                             Dir   #Shrs  Entry Dt   Exit Dt Entry Px  Exit Px  Entry $   Exit $      P&L   Return'
    print '-----------------------------------------------------------------------------------------------------------------------------'
    numOpenTrades = len(flatten(openTradePerformances))
    if numOpenTrades == 0:
        print 'None'
    else:
        for openTrades in openTradePerformances:
            for p in openTrades:
                p.entryDate = dates[dates.index(p.entryDate) + 1]
                print str(p)
    print
    print '-----------------------------------------------------------------------------------------------------------------------------'
    print 'Closed Trades                           Dir   #Shrs  Entry Dt   Exit Dt Entry Px  Exit Px  Entry $   Exit $      P&L   Return'
    print '-----------------------------------------------------------------------------------------------------------------------------'
    numClosedTrades = len(flatten(closedTradePerformances))
    if numClosedTrades == 0:
        print 'None'
    else:
        for closedTrades in closedTradePerformances:
            for p in closedTrades:
                p.entryDate = dates[dates.index(p.entryDate) + 1]
                p.exitDate = dates[dates.index(p.exitDate) + 1]
                print str(p)

    totTradePerformances = openTradePerformances + closedTradePerformances
    totEntryAmount = sum([p.entryAmount for p in flatten(totTradePerformances)])
    totCurrentAmount = sum([p.currentAmount for p in flatten(totTradePerformances)])
    totRetAmount = sum([p.retAmount for p in flatten(totTradePerformances)])
    totRet = 100.0 * totRetAmount / totEntryAmount

    # Append return to historical performance file (if not already there for that date)
    filename = market + '-port-ret.csv'
    portRets = []
    f = open(filename)
    for line in f:
        data = line.strip().split(',')
        portRet = portfolioReturn(market, data[0], float(data[1]), float(data[2]), float(data[3]), float(data[4].replace('%', '')))
        portRets.append(portRet)
    f.close()
    portRetDates = [portRet.date for portRet in portRets]
    if getMatchStr(str(asofDate)) not in portRetDates:
        f = open(filename, 'a')
        portRet = portfolioReturn(market, getMatchStr(str(asofDate)), totEntryAmount, totCurrentAmount, totRetAmount, totRet)
        f.write(portRet.toCsv() + '\n')
        portRets.append(portRet)
        f.close()

    # Now print portfolio returns for all dates
    print
    print '-----------------------------------------'
    print 'Performance  Invested        P&L   Return'
    print '-----------------------------------------'
    dates = []
    rets = []
    for portRet in portRets:
        print str(portRet)
        dates.append(portRet.date)
        rets.append(portRet.totRet)

    # Create chart
    import matplotlib
    matplotlib.use('Agg')   # Don't use X server on Unix (otherwise crashes because DISPLAY is not defined)
    import matplotlib.pyplot as plt
    plt.plot(rets)
    locs, labels = plt.xticks(range(len(rets)), dates, size='small')
    plt.setp(labels, rotation=90)
    plt.ylabel('Artemis ' + market + ' Return (%)')
    plt.axes().yaxis.grid()
    #plt.savefig(market + '-plot.png', bbox_inches='tight')
    filename = market + '-plot.pdf'
    from matplotlib.backends.backend_pdf import PdfPages
    pp = PdfPages(filename)
    pp.savefig(bbox_inches='tight')
    pp.close()

    # Auto update Excel file (experimental)
    AUTO_UPDATE = False
    if AUTO_UPDATE:
        filename = 'portfolio-artemis-us-test.xlsx'
        wb = load_workbook(filename)
        sheet = wb.get_sheet_by_name('Email')
        newTradeRanges = ['open_long', 'close_long', 'open_short', 'close_short']
        newTradePerformances = [[p for p in performances if p.entryDate == asofDate and p.direction == 'Long'],
                                [p for p in performances if p.exitDate == asofDate and p.direction == 'Long'],
                                [p for p in performances if p.entryDate == asofDate and p.direction == 'Short'],
                                [p for p in performances if p.exitDate == asofDate and p.direction == 'Short']]
        for i in range(len(newTradeRanges)):
            #namedRange = rb.name_and_scope_map.get((newTradeRanges[i], -1))
            j = 0
            for performance in newTradePerformances[i]:
                pass
        #sheet["'" + cellStr[cellStr.find('!') + 1:] + "'"] = 'AAPL'
        sheeet = wb.get_sheet_by_name('Email')
        sheet['D8'] = 'AAPL'
        wb.save('a.xlsx')
