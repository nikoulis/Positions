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

    NUM_SAMPLE_POSITIONS = 100

    # Read benchmark portfolio
    benchmarkPortfolio = Portfolio(market)
    benchmarkPortfolio.readCsv(getMarket(market) + '-' + str(asofDate) + '.csv')

    # Exclude symbols in foreign markets, or without sectors, or without market caps,
    # or where market cap < $5bn (for the US portfolio only)
    stockInfoHash = readSectorFile(getMarket(market))
    sectorSymbols = [s for s in stockInfoHash.keys()
                     if (s.find('.') == -1 or getMarket(market) == 'LSE') and
                     stockInfoHash[s].sector != '' and 
                     (stockInfoHash[s].marketCapNum > 5000 or getMarket(market) == 'LSE')]
    benchmarkPortfolio.positions = [p for p in benchmarkPortfolio.positions if p.symbol in sectorSymbols]
    # Calculate sector percentages and sample accordingly
    benchmarkSectorPositions, benchmarkSectorPercent = calcSectorPercent(benchmarkPortfolio, stockInfoHash)
    benchmarkPortfolio.showStats(stockInfoHash)
    samplePortfolio = Portfolio(market)
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
    benchmarkPortfolio.showStats(stockInfoHash)
    print
    samplePortfolio.showStats(stockInfoHash)

    # Save portfolio to file for future reference
    samplePortfolio.writeCsv(market + '-sample.csv')
