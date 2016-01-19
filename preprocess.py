import sys
sys.path.append('/home/nikoulis/anaconda/lib/python2.7/site-packages')  # For Ubuntu
import os
import pdb
from diffs import *
from shutil import copyfile

#-------------------------------------------------------------------------
# Update dates file and make sure all benchmark files are updated as well
#-------------------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: preprocess.py <US/LSE>'
        sys.exit()

    market = sys.argv[1]
    #portfolio = Portfolio(market)
    #portfolio.readMail('P 14-Oct-15')
    #pdb.set_trace()

    dates = updateDates(market)
    for date in dates:
        filename = getMarket(market) + '-' + str(date) + '.csv'
        if not os.path.exists(filename):
            print 'Saving', filename
            benchmarkPortfolio = readPortfolio(market, date, 'Yahoo')
            benchmarkPortfolio.writeCsv(filename)
