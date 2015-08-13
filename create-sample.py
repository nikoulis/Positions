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

    benchmarkPortfolio = Portfolio()
    benchmarkPortfolio.readCsv(market + '-' + asofDate + '.csv')
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
    print
    showStats(samplePortfolio, sectors)

    # Save portfolio to file for future reference
    samplePortfolio.writeCsv(market + '-sample.csv')
