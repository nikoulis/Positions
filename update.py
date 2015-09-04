import sys
from diffs import *

#==========================================================================================#
# Run update.py after inspecting the output of diffs.py and intervening manually if needed #
#==========================================================================================#

#------------------------------------------
# Read the diffs file and update portfolio
#------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: update.py <US/LSE> <yyyymmmdd>'
        sys.exit()

    market = sys.argv[1]
    if len(sys.argv) >= 3:
        asofDate = sys.argv[2]
    else:
        # Use last date from file
        dates = getDates(market)
        asofDate = dates[-1]
    
    # Read current global portfolio
    portfolio = Portfolio(market)
    portfolio.readCsv(market + '-portfolio.csv')

    portfolio.update(asofDate)
