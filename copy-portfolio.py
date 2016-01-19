import sys
sys.path.append('/home/nikoulis/anaconda/lib/python2.7/site-packages')  # For Ubuntu
import time
from diffs import *
import pdb
from shutil import copyfile

#------------------------------------------------------------------
# Copy portfolio file from yesterday (only used for LSE currently)
#------------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: preprocess.py <US/LSE>'
        sys.exit()

    market = sys.argv[1]
    currentDate = int(time.strftime('%Y%m%d'))

    # Don't run if it's a holiday
    filename = getMarket(market) + '-holidays.csv'
    f = open(filename)
    for line in f:
        date = int(line.strip())
        if date == currentDate:
            print str(currentDate) + ' is a holiday.'
            sys.exit()

    # Copy previous file (we are using sample anyway, so it doesn't matter;
    # had we used actual daily trades, this would just disable them, which is OK)
    # This needs to run at the end of each day, assuming it's not a holiday
    dates = getDates(market)
    date = dates[-1]
    filename = getMarket(market) + '-' + str(date) + '.csv'
    newFilename = getMarket(market) + '-' + str(currentDate) + '.csv'
    copyfile(filename, newFilename)
    f = open(getMarket(market) + '-dates.csv', 'a')
    f.write(str(currentDate) + '\n')
    f.close()
