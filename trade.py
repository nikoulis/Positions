from yahoo_finance import Share
import urllib2
import pdb

positionAmount = 250
#systemId = '94442625'    # test9999
systemId = '94428681'   # Momentum Stock Trading

trades = (
'Long TOWN',
'Long PLAY',
'Long STJ',
'Short DMLP',
)

for trade in trades:
    period = trade.find(' ')
    direction = trade[:period]
    symbol = trade[period + 1:]
    if direction == 'Long':
        action = 'BTO'
    elif direction == 'Short':
        action = 'SSHORT'
    else:
        action = direction

    stock = Share(symbol)
    px = stock.get_prev_close()
    price = float(px)
    numShares = max(1, round(positionAmount / price / 5)) * 5     # Only do multiples of 5
    period = symbol.find('.AX')   # Australian Stock Exchange
    if period > 0:
        symbol = 'ASX.' + symbol[:period]

    url = 'http://www.collective2.com/cgi-perl/signal.mpl?cmd=signal&systemid=%s&pw=RustyKnot&instrument=stock&action=%s&quant=%.0f&symbol=%s&duration=DAY' % (systemId, action, numShares, symbol)
    print symbol, price, url

    # Header is needed to put the request thorugh (otherwise, you get a 403 error)
    request = urllib2.Request(url, headers={'User-Agent' : "Magic Browser"}) 
    response = urllib2.urlopen(request)
    html = response.read()
    print html
