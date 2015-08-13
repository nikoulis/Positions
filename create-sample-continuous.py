from diffs import *
from sectors import *
import sys
import random

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

    # Read current portfolio
    sectors = readSectorFile()
    portfolio = Portfolio()
    portfolio.readCsv(market + '-portfolio.csv')
    sectorPositions, sectorPercent = calcSectorPercent(portfolio, sectors)

    # Read benchmark portfolio and find all symbols that are not in current portfolio
    NUM_SAMPLE_POSITIONS = 100
    benchmarkPortfolio = Portfolio()
    benchmarkPortfolio.readCsv(market + '-' + asofDate + '.csv')
    diffs = Diffs(portfolio, benchmarkPortfolio)
    remainingPortfolio = Portfolio()
    remainingPortfolio.positions = diffs.newPositions
    remainingSectorPositions, remainingSectorPercent = calcSectorPercent(remainingPortfolio, sectors)

    # Calculate sector percentages in benchmark portfolio and sample accordingly (excluding current positions)
    benchmarkSectorPositions, benchmarkSectorPercent = calcSectorPercent(benchmarkPortfolio, sectors)
    showStats(benchmarkPortfolio, sectors)
    samplePortfolio = Portfolio()
    for sectorName in remainingSectorPositions.keys():
        for direction in remainingSectorPositions[sectorName]:
            remainingPositions = remainingSectorPositions[sectorName][direction]
            numRemainingPositions = len(remainingPositions)
            if numRemainingPositions > 0:
                numSamplePositions = max(1, int(float(NUM_SAMPLE_POSITIONS) * 
                                                float(benchmarkSectorPercent[sectorName][direction]) / 
                                                100.0))
                numPortfolioPositions = len(sectorPositions[sectorName][direction])
                numBenchmarkPositions = len(benchmarkSectorPositions[sectorName][direction])
                print ('%s %s (pick %d out of %d positions, exclude %d positions)') % (sectorName,
                                                                                       direction,
                                                                                       numSamplePositions - numPortfolioPositions,
                                                                                       numBenchmarkPositions,
                                                                                       numPortfolioPositions)
                positionIndices = random.sample(xrange(numRemainingPositions), numSamplePositions - numPortfolioPositions)
                samplePositions = [remainingPositions[i] for i in positionIndices]
                for position in samplePositions:
                    print str(position)
                samplePortfolio.positions.extend(samplePositions)
    print
    showStats(samplePortfolio, sectors)

    # Save portfolio to file for future reference
    samplePortfolio.writeCsv(market + '-sample.csv')

    # Make a backup as always
    currentTime = time.strftime('%Y%m%d-%H-%M-%S')
    samplePortfolio.writeCsv(market + '-sample-' + currentTime + '.csv')
