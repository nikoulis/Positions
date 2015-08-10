import sys
from sectors import *

symbols = ['VIV.P',
'FNC.MI',
'STFC',
'UFCS',
'HTBK',
'FICO',
'TI',
'JRVR',
'OUBSF,',
'SKY.L',
'COH',
'DLB',
'SUN',
'MKTO',
'PPC',
'RPC.L',
'BBOX.L',
'CLIN.L',
'JDW.L',
]

for symbol in symbols:
    name, marketCap, sector, industry = getYahooFinanceData(symbol)
    print symbol, name, marketCap, sector, industry
