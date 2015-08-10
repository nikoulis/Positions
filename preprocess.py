import sys
import os
import pdb
from diffs import *

#-------------------------------------------------------------------------
# Update dates file and make sure all benchmark files are updated as well
#-------------------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: preprocess.py <US/LSE>'
        sys.exit()

    market = sys.argv[1]
    dates = updateDates(market)
    for date in dates:
        filename = market + '-' + str(date) + '.csv'
        if not os.path.exists(filename):
            print 'Saving', filename
            benchmarkPortfolio = readPortfolio(market, date, 'Yahoo')
            benchmarkPortfolio.writeCsv(filename)
