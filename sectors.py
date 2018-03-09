# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import codecs             # For saving utf8 characters in company names (e.g. Estee Lauder)
import re                 # Regular expressions, for use in Beautiful Soup matching
import sys
import pdb

#-----------------------------------------------------
# Convert market cap from yahoo finance into a number
#----------------------------------------------------
def getMarketCapNum(marketCap):
    try:
        indexMillion = marketCap.index('M')
    except ValueError:
        indexMillion = 'Error'
    try:
        indexBillion = marketCap.index('B')
    except ValueError:
        indexBillion = 'Error'
    if indexBillion != 'Error':
        return float(marketCap[:indexBillion]) * 1000.0
    elif indexMillion != 'Error':
        return float(marketCap[:indexMillion])
    else:
        return ''

#---------------------------------
# Get market cap from an href tag
#---------------------------------
def getMarketCap(tag, element='span'):
    result = ''
    if tag != None:
        tag = tag.parent
        if tag != None:
            tag = tag.parent
            if tag != None:
                tag = tag.findNextSibling()
                if tag == None:
                    result = '0B'
                else:
                    if tag.contents != []:
                        result = tag.contents[0]
    if not isinstance(result, unicode):
        result = '0B'
    return result

#------------------------
# Get sector or industry
#------------------------
def getData(tag, element='span'):
    result = ''
    if tag != None:
        tag = tag.parent
        if tag != None:
            tag = tag.findNextSibling()
            if tag == None:
                result = ''
            else:
                if tag.contents != []:
                    result = tag.contents[0]
    return result

#------------------------------------------------
# Normalize symbol to match Yahoo Finance format
#------------------------------------------------
def normalizeSymbol(symbol):
    # Toronto Stock Exchange
    period = symbol.find('-U')
    if period > 0:
        symbol = symbol[:period] + '-UN.TO'
    # Toronto Stock Exchange
    period = symbol.find('.T')
    if period > 0:
        symbol = symbol[:period] + '.TO'
    # Deutsche Boerse AG
    period = symbol.find('.D')
    if period > 0:
        symbol = symbol[:period] + '.DE'
    # VTX (SIX Swiss Stock Exchange)
    period = symbol.find('.V')
    if period > 0:
        symbol = symbol[:period] + '.VX'
    # Paris Stock Exchange
    period = symbol.find('.P')
    if period > 0:
        symbol = symbol[:period] + '.PA'
    return symbol

#--------------------------------------------------------------------
# Get stock name, market cap, sector and industry from Yahoo Finance
#--------------------------------------------------------------------
def getYahooFinanceData(symbol):
    symbol = normalizeSymbol(symbol)
    # Get name and market cap
    url = 'http://finance.yahoo.com/quote/' + symbol + '/key-statistics?ltr=1'
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'lxml')
    tag = soup.find(text=re.compile('Market Cap'))
    marketCap = getMarketCap(tag)
    tag = soup.findAll('h1')
    name = ''
    if tag != []:
        tag = tag[0]
        if tag != None:
            tag = tag.contents
            if tag != []:
                name = tag[0]

    name = name.replace('(' + symbol + ')', '')    # Take out symbol from nane
    name = name.strip()

    # Get sector and industry
    url = 'http://finance.yahoo.com/q/in?s=' + symbol + '?p=' + symbol
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'lxml')
    tag = soup.find(text=re.compile('Sector'))
    sector = getData(tag, 'a')
    tag = soup.find(text='Industry')
    industry = getData(tag, 'a')

    return name, sector, industry, marketCap

#-------------------------------------------------------------------
# Get name, sector, industry and market cap for a list of companies
#-------------------------------------------------------------------
if __name__ == '__main__':

    if len(sys.argv) < 2:
        print 'Usage: %s <filename>' % sys.argv[0]
        sys.exit()
        
    filename = sys.argv[1]
    f = codecs.open(filename, 'r', 'utf-8')

    CREATE_OUTPUT_FILE = True
    if CREATE_OUTPUT_FILE:
        out = codecs.open('sectors-%s' % filename, 'w', 'utf-8')

    i = 1
    for line in f:
        data = line.split(',')
        symbol = data[0].strip()
        name, sector, industry, marketCap = getYahooFinanceData(symbol)

        if CREATE_OUTPUT_FILE:
            print 'Running #%d (%s)' % (i, symbol)
            out.write(symbol  + '|' + name + '|' + sector + '|' + industry + '|' + marketCap + '\n')
            out.flush()
        else:
            print '%s|%s|%s|%s|%s' % (symbol, name, sector, industry, marketCap)
        i += 1
