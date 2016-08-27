# -*- coding: utf-8 -*-
"""
Created on Mon Jul 25 16:04:21 2016

@author: Phill
"""
import basefunc as JMTB
import dbfunc as JMDB
import indicators as JMTI
import time
import logging


logging.basicConfig(format='%(asctime)s %(message)s',datefmt='%m/%d/%Y %I:%M:%S %p',filename='JMTB.log',level=logging.DEBUG)


#Start splash screen.      
start=time.time()
#JMTB.splash()
JMDB.createDatabase()
JMDB.updateCurrentPos(JMTB.snapshot(JMTB.getTicker(),JMTB.getBalance(),JMTB.returnOpenOrders()))
for coin in JMTB.searchCoins:JMDB.createTradeTable(coin)
x=0
while True:
#Check trailing stop first and foremost. JMTI.checkTrailingStop will return a list of all coins which have hit their T_Stop
#Loss and need to be sold.  The sell mechanics have not been added yet. 
    if x >= JMTB.data['System']['Num_of_Cycles']:
        persistence=JMTB.data['System']['persistence']        
        if persistence == 0: break  
    x+=1
    logging.warning('--------------------')
    logging.warning('Cycle {} begin.'.format(x))
    check=JMTI.checkTrailingStop()
    if not check:
        logging.warning("No coins hit trailing stop")
    elif check: 
        logging.warning("Trailing stop hit by: {}".format(check))

        cp=JMDB.getCurrentPosDB() 
        for coin in check:
            logging.warning(cp.loc[coin])
            logging.warning("Sell value is {}".format((cp.loc[coin]['Price']*cp.loc[coin]['Balance'])))
            JMTB.sell(coin,cp.loc[coin]['Price'],cp.loc[coin]['Balance'])
    if (x % 5 == 0) or (x == 1):
       #Update chart data as required. Every five cycles chart data will be checked for timetstamp and updated if required. 
        if x!=1:
            JMDB.updateCurrentPos(JMTB.snapshot(JMTB.getTicker(),JMTB.getBalance(),JMTB.returnOpenOrders()))
        for coin in JMTB.searchCoins:
            settings=JMTB.coinSettings(coin)
            period=settings['period']
            breakout=settings['enable_breakout']
            holding=settings['enable_hold_pos'] 
            pivot=settings['enable_pivot']
            test=settings['test_trade']
            
            if JMTB.syncChartData(coin,period):
                logging.debug("\tUpdating Indicators for {} with period {}".format(coin,period))
                JMDB.writeIndicators(JMTI.setIndicators(JMDB.readChartData(coin,period)),coin,period)
            JMTI.setTrailingStop(coin,period)
            JMDB.writePivotPoints(JMTI.setPivotPoints(coin,period),coin,period)
            if test:
                logging.warning("######################### {} is in TEST MODE @@@@@TESTMODE@@@@@@".format(coin))
                JMTB.testTrade(coin)
                continue
            if breakout:
                logging.warning("~~~~~~~~ {} is trading BREAKOUT ~~~~~~~~~".format(coin))                
                JMTI.checkBreakout(coin,period)
                
            if holding:          
                logging.warning('{} is trading a holding strategy.'.format(coin))
                JMTI.checkHolding(coin, period)
            
            if pivot:
                JMTI.checkPivotPoint(coin, period)
            


    print "Cycle ",x,"complete"        
    logging.warning("Cycle {} complete".format(x))
    logging.warning("----------------------------")
    time.sleep(JMTB.data['System']['Pause_Duration'])
    
JMTB.splash()    
print "Completion time in seconds: ", time.time() - start
JMDB.conn.close() 
