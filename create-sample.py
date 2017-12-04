from diffs import *
from sectors import *
import sys
import random

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: create-sample.py <US/LSE> [<yyyymmmdd>]'
        sys.exit()

    market = sys.argv[1]
    if len(sys.argv) >= 3:
        asofDate = sys.argv[2]
    else:
        # Use last date from file
        dates = getDates(market)
        asofDate = dates[-1]

    NUM_SAMPLE_POSITIONS = 200

    # Read benchmark portfolio
    benchmarkPortfolio = Portfolio(market)
    benchmarkPortfolio.readCsv(getMarket(market) + '-' + str(asofDate) + '.csv')
    stockInfoHash = readSectorFile(getMarket(market), asofDate)

    # Show initial sector percentages
    benchmarkPortfolio.showStats(stockInfoHash)
    
    # Exclude symbols in foreign markets, or without sectors, or without market caps,
    # or where market cap < $5bn (for the US portfolio only)
    sectorSymbols = [s for s in stockInfoHash.keys()
                     if (s.find('.') == -1 or getMarket(market) == 'LSE') and
                     stockInfoHash[s].sector != '' and 
                     (stockInfoHash[s].marketCapNum > 25000 or getMarket(market) == 'LSE')]

    # Delete _0 from symbols so that the below filter works
    for p in benchmarkPortfolio.positions:
        p.symbol = p.symbol[:p.symbol.find('_0')]

    # Select only positions that pass the above conditions
    benchmarkPortfolio.positions = [p for p in benchmarkPortfolio.positions if p.symbol in sectorSymbols]
    
    # Add back _0 to symbols so that the calcSectorPercent works
    for p in benchmarkPortfolio.positions:
        p.symbol = p.symbol + '_0'
    
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
    samplePortfolio.showStats(stockInfoHash)

    # Save portfolio to file for future reference
    samplePortfolio.writeCsv(market + '-sample-test.csv')
