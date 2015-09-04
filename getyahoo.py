import sys
from sectors import *
from diffs import *
import codecs

#------------------------------------------------------------------
# Read a portfolio, get names, sectors, industries and market caps
# for its symbols and save in sectors file (if not already there)
#------------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: getyahoo.py <US/LSE> <yyyymmmdd>'
        sys.exit()
        
    market = sys.argv[1]
    if len(sys.argv) >= 3:
        asofDate = sys.argv[2]
    else:
        # Use last date from file
        dates = getDates(market)
        asofDate = dates[-1]
    print 'asofDate =', asofDate
    
    portfolio = Portfolio(market)
    portfolio.readCsv(market + '-' + str(asofDate) + '.csv')

    currentStockInfoHash = readSectorFile(market)
    currentSymbols = currentStockInfoHash.keys()

    f = codecs.open('sectors-' + market + '.txt', 'a', 'utf-8')
    for position in portfolio.positions:
        symbol = position.symbol
        if not symbol in currentSymbols:
            name, sector, industry, marketCap = getYahooFinanceData(symbol)
            marketCapNum = getMarketCapNum(marketCap)
            print symbol, name, sector, industry, marketCap, marketCapNum
            f.write(symbol + '|' + name  + '|' + sector + '|' + industry + '|' + marketCap + '|' + str(marketCapNum) + '\n')
    f.close()
