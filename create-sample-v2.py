from diffs import *
from sectors import *
import sys
import random

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: create-sample-v2.py <US/LSE> <yyyymmmdd>'
        sys.exit()

    market = sys.argv[1]
    if len(sys.argv) >= 3:
        asofDate = sys.argv[2]
    else:
        # Use last date from file
        dates = getDates(market)
        asofDate = dates[-1]

    # Read benchmark portfolio
    benchmarkPortfolio = Portfolio(market)
    benchmarkPortfolio.readCsv(market + '-' + str(asofDate) + '.csv')

    # Exclude symbols in foreign markets, or without sectors, or without market caps,
    # or where market cap < $5bn (for the US portfolio only)
    stockInfoHash = readSectorFile(market)
    sectorSymbols = [s for s in stockInfoHash.keys()
                     if (s.find('.') == -1 or market == 'LSE') and
                     stockInfoHash[s].sector != '' and 
                     (stockInfoHash[s].marketCapNum > 5000 or market == 'LSE')]
    benchmarkPortfolio.positions = [p for p in benchmarkPortfolio.positions if p.symbol in sectorSymbols]

    # Read index portfolio (S&P 100 or FTSE 100) and find common symbols
    indexPortfolio = Portfolio(market)
    indexPortfolio.readCsv(market + '-index.csv')
    indexSymbols = [p.symbol for p in indexPortfolio.positions]
    diffs = Diffs(benchmarkPortfolio, indexPortfolio)
    samplePortfolio = Portfolio(market)
    samplePortfolio.positions = [p for p in benchmarkPortfolio.positions if p.symbol in indexSymbols]

    # Show stats
    print
    benchmarkPortfolio.showStats(stockInfoHash)
    print
    samplePortfolio.showStats(stockInfoHash)

    # Save portfolio to file for future reference
    samplePortfolio.writeCsv(market + '-sample-v2.csv')
