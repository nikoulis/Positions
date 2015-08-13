import sys
from sectors import *
from diffs import *

#------------------------------------------------------------------
# Read a portfolio and get sectors and market caps for its symbols
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
    
    # Get sector, industry and market cap for current portfolio
    portfolio = Portfolio()
    portfolio.readCsv(market + '-' + str(asofDate) + '.csv')

    f = open('sectors-' + market + '.txt', 'w')
    for position in portfolio.positions:
        symbol = position.symbol
        name, sector, industry, marketCap = getYahooFinanceData(symbol)
        print symbol, name, sector, industry, marketCap
        f.write(symbol + '|' + name  + '|' + sector + '|' + industry + '|' + marketCap + '\n')
    f.close()
