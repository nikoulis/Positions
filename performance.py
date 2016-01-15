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
    dates = getDates(getMarket(market))
    if len(sys.argv) >= 3:
        asofDate = sys.argv[2]
    else:
        # Use last date from file
        asofDate = dates[-1]

    # Don't run if it's a holiday
    currentDate = int(time.strftime('%Y%m%d'))
    filename = getMarket(market) + '-holidays.csv'
    f = open(filename)
    holidays = []
    for line in f:
        holiday = int(line.strip())
        holidays.append(holiday)
    if currentDate in holidays:
        print str(currentDate) + ' is a holiday.'
        sys.exit()

    # Don't run if today's becnhmark file hasn't been saved (this can happen if today's email doesn't arrive
    # by the time preprocess.py runs, or if the email subject is wrong); in that case, the performance
    # report isn't updated either.  If preprocess.py doesn't find a new email to save (and to update the
    # dates.csv file), then yesterday's benchmark file will still be there, saved with yesterday's date.
    filename = getMarket(market) + '-' + str(asofDate) + '.csv'
    fileSavedDate = int(datetime.strptime(time.ctime(os.path.getctime(filename)), "%a %b %d %H:%M:%S %Y").strftime('%Y%m%d'))
    if fileSavedDate != currentDate and fileSavedDate not in holidays:
        sys.exit()

    #asofDate = time.strftime('%Y%m%d')
    portfolio = Portfolio(market)
    portfolio.readCsv(market + '-portfolio.csv')

    # Download prices and calculate performance
    startDate = datetime(*getDateComponents(str(min([p.entryDate for p in portfolio.positions]))))
    endDate = datetime(*getDateComponents(str(asofDate)))
    DOWNLOAD = True
    if DOWNLOAD:
        portfolio.downloadPrices(startDate, endDate)
    if market == 'US':
        inceptionDate = 20151007
    elif market == 'LSE':
        inceptionDate = 20150923
    elif market == 'US-tradehero':
        inceptionDate = 20151023
    elif market == 'LSE-tradehero':
        inceptionDate = 20151023
    FULL = False
    if FULL:
        startDateIndex = 0
    else:
        startDateIndex = dates.index(inceptionDate)
    date = asofDate

    # From this point on, redirect output to file
    filename = market + '-perf-' + str(asofDate) + '.txt'
    sys.stdout = open(filename, 'w')

    if market == 'US-tradehero' or market == 'LSE-tradehero':
        verbose = False
    else:
        verbose = True

    #---------------------------------------------
    # Calculate portfolio returns since inception
    #---------------------------------------------
    DISPLAY_CALC_RETS = False
    if DISPLAY_CALC_RETS:
        calcPortRets = []
        startIndex = dates.index(inceptionDate)
        endIndex = dates.index(asofDate) + 1
        for i in range(startIndex, endIndex):
            if market == 'US' or market == 'LSE':
                if i == endIndex - 1:
                    verbose = True
                else:
                    verbose = False
            totEntryAmount, totCurrentAmount, totRetAmount, totRet, performances = portfolio.calcPerformance(dates[i], verbose)

            openTradePerformances = [p for p in performances if p.entryDate < dates[i] and (p.exitDate == '' or p.exitDate == dates[i])]
            closedTradePerformances = [p for p in performances if p.entryDate < dates[i] and p.exitDate != '' and p.exitDate < dates[i]]

            totTradePerformances = openTradePerformances + closedTradePerformances
            totEntryAmount = sum([p.entryAmount for p in totTradePerformances])
            totCurrentAmount = sum([p.currentAmount for p in totTradePerformances])
            totRetAmount = sum([p.retAmount for p in totTradePerformances])
            if totEntryAmount == 0:
                totRet = 0
            else:
                totRet = 100.0 * totRetAmount / totEntryAmount

            calcPortRet = PortfolioReturn(market, getMatchStr(str(dates[i])), totEntryAmount, totCurrentAmount, totRetAmount, totRet)
            calcPortRets.append(calcPortRet)
    else:
        totEntryAmount, totCurrentAmount, totRetAmount, totRet, performances = portfolio.calcPerformance(asofDate, verbose)

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
    stockInfoHash = readSectorFile(getMarket(market))

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
            print '-----------------------------------------------------------------------------------------------------------------------------'
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
            print '-----------------------------------------------------------------------------------------------------------------------------'

    totTradePerformances = openTradePerformances + closedTradePerformances
    totEntryAmount = sum([p.entryAmount for p in flatten(totTradePerformances)])
    totCurrentAmount = sum([p.currentAmount for p in flatten(totTradePerformances)])
    totRetAmount = sum([p.retAmount for p in flatten(totTradePerformances)])
    if totEntryAmount == 0:
        totRet = 0
    else:
        totRet = 100.0 * totRetAmount / totEntryAmount

    #-----------------------------------------------------------------------------------
    # Append return to historical performance file (if not already there for that date)
    #-----------------------------------------------------------------------------------
    filename = market + '-port-ret.csv'
    portRets = []
    f = open(filename)
    for line in f:
        data = line.strip().split(',')
        portRet = PortfolioReturn(market, data[0], float(data[1]), float(data[2]), float(data[3]), float(data[4].replace('%', '')))
        portRets.append(portRet)
    f.close()
    portRetDates = [portRet.date for portRet in portRets]
    if getMatchStr(str(asofDate)) not in portRetDates:
        f = open(filename, 'a')
        portRet = PortfolioReturn(market, getMatchStr(str(asofDate)), totEntryAmount, totCurrentAmount, totRetAmount, totRet)
        f.write(portRet.toCsv() + '\n')
        portRets.append(portRet)
        f.close()

    #-------------------------------------------------------
    # Print portfolio returns for all dates since inception
    #-------------------------------------------------------
    print
    print '-----------------------------------------'
    print 'Performance  Invested        P&L   Return'
    print '-----------------------------------------'

    # Using stored values in port-ret.csv file
    DISPLAY_STORED_RETS = True
    if DISPLAY_STORED_RETS:
        dates = [getMatchStr(str(inceptionDate))]
        rets = [0]
        for portRet in portRets:
            print str(portRet)
            dates.append(portRet.date)
            rets.append(portRet.totRet)

    # Using calculated values
    if DISPLAY_CALC_RETS:
        print
        calcDates = []
        calcRets = []
        for i in range(1, len(calcPortRets)):
            print str(calcPortRets[i])
            calcDates.append(calcPortRet.date)
            calcRets.append(calcPortRet.totRet)

    #--------------
    # Create chart
    #--------------
    import matplotlib
    matplotlib.use('Agg')   # Don't use X server on Unix (otherwise crashes because DISPLAY is not defined)
    import matplotlib.pyplot as plt
    plt.figure(figsize=(11, 8.5))
    plt.plot(rets)
    locs, labels = plt.xticks(range(len(rets)), dates, size='small')
    plt.setp(labels, rotation=90)
    plt.ylabel('Artemis ' + market + ' Return (%)')
    plt.axes().yaxis.grid()
    #plt.savefig(market + '-plot.png', bbox_inches='tight')
    filename = market + '-plot.pdf'
    from matplotlib.backends.backend_pdf import PdfPages
    pp = PdfPages(filename)
    pp.savefig(papersize='letter', orientation='landscape', bbox_inches='tight', pad_inches=1)
    pp.close()


    """
    # Auto update Excel file (highly experimental -- don't use)
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
    """
