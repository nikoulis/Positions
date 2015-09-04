from diffs import *
from sectors import *
import sys
import random

#--------------------------------------------------------------------------
# Remove positions from sample portfolio if needed (based on daily diffs)
# (positions in actual portfolio are removed anyway in the update function
#--------------------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: create-sample.py <US/LSE> <yyyymmmdd>'
        sys.exit()

    market = sys.argv[1]
    if len(sys.argv) >= 3:
        asofDate = sys.argv[2]
    else:
        # Use last date from file
        dates = getDates(market)
        asofDate = dates[-1]

    # Read current sample portfolio and sector file
    samplePortfolio = Portfolio(market)
    samplePortfolio.readCsv(market + '-sample.csv')
    stockInfoHash = readSectorFile(market)

    # Sample file was created as of 20150811; check all removed positions since then
    startDateIndex = dates.index(20150812)
    for date in dates[startDateIndex:]:
        print 'Checking removals for', date
        positionsNew, positionsRemoved = readDiffs(market + '-diffs-' + str(date) + '.csv')
        removedPositions = [p for p in samplePortfolio.positions if p in positionsRemoved]
        for position in removedPositions:
            samplePortfolio.positions.pop(samplePortfolio.positions.index(position))
            print 'Removed ' + str(position)
        samplePOrtfolio.showStats(stockInfoHash)

    # Save portfolio to file for future reference
    samplePortfolio.writeCsv(market + '-sample.csv')
