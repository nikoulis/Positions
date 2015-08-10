import sys
from diffs import *
from sectors import *
import random

#-----------------------------------------------------------
# Read the diffs, update portfolio and calculate statistics
#-----------------------------------------------------------
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

    # Read current portfolio
    portfolio = Portfolio()
    portfolio.readCsv(market + '-portfolio.csv')

    # Read diffs file
    f = open(market + '-diffs-' + asofDate + '.csv')
    positionsNew = []
    positionsRemoved = []
    for line in f:
        data = line.strip().split(',')
        action = data[0]
        direction = data[1]
        symbol = data[2]
        position = Position(direction, symbol)
        if action == 'New':
            positionsNew.append(position)
        else:
            positionsRemoved.append(position)

    # Add new positions to global portfolio, if not already there
    f = open(market + '-portfolio.csv', 'a')
    for p in positionsNew:
        p.entryDate = asofDate
        found = False
        for position in portfolio.positions:
            if (position.direction == p.direction and
                position.symbol == p.symbol and
                position.entryDate <= p.entryDate and
                position.exitDate == 0):
                found = True
                break
        if found:
            print 'Skipping', str(p)
        else:
            print 'Adding', str(p)
            f.write(str(p) + '\n')
            # Also update sectors file
            s = open(SECTOR_FILENAME, 'a')
            name, marketCap, sector, industry = getYahooFinanceData(p.symbol)
            marketCapNum = getMarketCapNum(marketCap)
            print p.symbol, name, marketCap, marketCapNum, sector, industry
            s.write(p.symbol + ',' + sector + ',' + str(marketCapNum) + '\n')
            s.close()
    f.close()

    # Set exit date for removed positions
    portfolio = Portfolio()
    portfolio.readCsv(market + '-portfolio.csv')
    newPortfolio = Portfolio()
    for position in portfolio.positions:
        found = False
        for p in positionsRemoved:
            if (position.direction == p.direction and
                position.symbol == p.symbol and
                position.exitDate == 0):
                found = True
                break
        if found:
            position.exitDate = asofDate
            print 'Set exitDate of', str(position)
        newPortfolio.positions.append(position)
    newPortfolio.writeCsv(market + '-portfolio.csv')

    # Read benchmark portfolio and calculate sector percentages
    NUM_SAMPLE_POSITIONS = 100
    benchmarkPortfolio = Portfolio()
    benchmarkPortfolio.readCsv(market + '-' + asofDate + '.csv')
    sectors = readSectorFile()
    benchmarkSectorPositions, benchmarkSectorPercent = calcSectorPercent(benchmarkPortfolio, sectors)
    showStats(benchmarkPortfolio, sectors)
    samplePortfolio = Portfolio()
    for sectorName in benchmarkSectorPositions.keys():
        for direction in benchmarkSectorPositions[sectorName]:
            benchmarkPositions = benchmarkSectorPositions[sectorName][direction]
            numBenchmarkPositions = len(benchmarkPositions)
            if numBenchmarkPositions > 0:
                numSamplePositions = max(1, int(float(NUM_SAMPLE_POSITIONS) * 
                                                float(benchmarkSectorPercent[sectorName][direction]) / 
                                                100.0))
                print ('%s %s (pick %d out of %d positions)') % (sectorName,
                                                                 direction,
                                                                 numSamplePositions,
                                                                 numBenchmarkPositions)
                positionIndices = random.sample(xrange(numBenchmarkPositions), numSamplePositions)
                samplePositions = [benchmarkPositions[i] for i in positionIndices]
                for position in samplePositions:
                    print str(position)
                samplePortfolio.positions.extend(samplePositions)
    print
    showStats(benchmarkPortfolio, sectors)
    showStats(samplePortfolio, sectors)

    # Save portfolio to file for future reference
    samplePortfolio.writeCsv(market + '-sample-0.csv')

    # Pick out from samplePortfolio until empty
    samplePortfolio = Portfolio()
    NUM_DAILY_POSITIONS = 2

    portfolio = Portfolio()
    i = 0
    while True:
        samplePortfolio.readCsv(market + '-sample-' + str(i) + '.csv')
        numSamplePositions = len(samplePortfolio.positions)
        if numSamplePositions > 0:
            print
            print 'Day ', i
            for j in range(min(numSamplePositions, NUM_DAILY_POSITIONS)):
                samplePosition = samplePortfolio.positions[j]
                portfolio.positions.append(samplePosition)
                del samplePortfolio.positions[j]
            showStats(portfolio, sectors)
            i += 1
            samplePortfolio.writeCsv(market + '-sample-' + str(i) + '.csv')
            portfolio.writeCsv(market + '-daily-' + str(i) + '.csv')
        else:
            break
