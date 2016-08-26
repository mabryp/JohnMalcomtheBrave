# -*- coding: utf-8 -*-
import dbfunc as JMDB
import pandas as pd
import basefunc as JMTB
import logging

def setIndicators(SMA):
    SMA['20SMA']=SMA.close.rolling(window=20,center=False).mean()
    SMA['30SMA']= SMA['close'].rolling(window=30,center=False).mean()
    SMA['BB_UP']= SMA['close'].rolling(window=20,center=False).mean() + (SMA['close'].rolling(min_periods=20,window=20,center=False).std()* 2)
    SMA['BB_LWR']= SMA['close'].rolling(window=20,center=False).mean() - (SMA['close'].rolling(min_periods=20,window=20,center=False).std()* 2)
    SMA['Highest_High']= SMA['high'].rolling(window=5,center=False).max()
    SMA['Lowest_Low'] = SMA['low'].rolling(window=5,center=False).min()
    return SMA

def setPivotPoints(coin,period):
    #Add the logic to figure out the M2-M4 day, or one for M1-M3 day.  Then on the strategy make better decisions.  
    df=JMDB.getLastCandlestick(coin,period)
    pp=round((df.high+df.low+df.close)/3,12)
    sup1=round((pp*2)-df.high,12)
    sup2=round(pp-(df.high-df.low),12)
    res1=round((pp*2)-df.low,12)
    res2=round(pp+(df.high-df.low),12)
    pivot={'pp':pp,'sup1':sup1,'sup2':sup2,'res1':res1,'res2':res2}
    return pivot

def currentIndicator(indicator,coin,period):
    data=JMDB.returnIndicators(coin,period)
    return data[indicator]
    
def setTrailingStop(coin,period):
    cpdf=JMDB.getCurrentPosDB()
    settings=JMTB.coinSettings(coin)
    disable_t_stop=settings['disable_t_stop']
    coin_t_stop = settings['trailing_stop']
    if (disable_t_stop==1) | (cpdf.loc[coin]['Balance']<=0.01):
        logging.warning("Tailing Stop disabled or zero balance for {}".format(coin))
        cpdf.set_value(coin,'Trailing_Stop',0)
        JMDB.updateTrailingStop(coin,0)
        return cpdf
    logging.warning("{} has trailing stop of {}.".format(coin,(100*coin_t_stop)))
    new_ts = round(cpdf.loc[coin]['Price'] * (1-coin_t_stop),9)
    old_ts = cpdf.loc[coin]['Trailing_Stop']
    if not old_ts:old_ts=0
    if new_ts >= (old_ts*1.02):
        logging.warning("Update Trailing Stop for {} to {}".format(coin,new_ts))
        cpdf.set_value(coin,'Trailing_Stop',new_ts)
        JMDB.updateTrailingStop(coin,new_ts)
        return cpdf
    elif new_ts < (old_ts*1.02):
        logging.warning("Do not update {} trailing stop.  Stay at {}".format(coin,old_ts))
        return cpdf
    else:
        logging.warning("No TrailingSTop set. Set to {}".format(new_ts))
        cpdf.set_value(coin,'Trailing_Stop',new_ts)
        JMDB.updateTrailingStop(coin,new_ts)
        return cpdf

def checkTrailingStop():#No input, outputs a list of coins which have hit their trailing stop.
    sellcoins=[]
    cpdf=JMDB.getCurrentPosDB()
    tick=JMTB.getTicker()   
    for coin in JMTB.searchCoins:
        settings=JMTB.coinSettings(coin)
        disable_t_stop=settings['disable_t_stop']
        if (disable_t_stop == 0) & (cpdf.loc[coin]['Trailing_Stop'] >= tick['Ticker:'+coin]['last']):
            sellcoins.append(coin)
           
    return sellcoins


def checkBreakout(coin, period):
    settings=JMTB.coinSettings(coin)
    period=settings['period']
    auth_amt=settings['auth_amt']
    cpdf=JMDB.getCurrentPosDB()
    cur_price=cpdf.loc[coin]['Price']
    balance=cpdf.loc[coin]['Balance']
    btc_bal=cpdf.loc[coin]['BTC_VAL']
    o_type=cpdf.loc[coin]['Type']
    highest_high=currentIndicator('Highest_High',coin,period)
    if o_type == 'Buy':
        logging.warning("Awaiting open orders.  Do not trade: ".format(coin))
        return 0  
    
    buy_price=cur_price*1.0002
    max_buy_quant=(btc_bal-auth_amt)/buy_price    
    total = round(max_buy_quant*buy_price,8)
    '''begin breakout trading logic'''
    if (highest_high[0]<(cur_price*1.02))&(total >= .01):
        logging.warning("BREAKOUT for: {}".format(coin))      
        #JMTB.buy(coin,max_buy_quant,buy_price)
    else: logging.warning("No breakout for {} identified.".format(coin))
    

def checkHolding(coin, period):

    cpdf=JMDB.getCurrentPosDB()
    auth_amt=cpdf.loc[coin]['Auth_BTC']
    cur_price=cpdf.loc[coin]['Price']
    balance=cpdf.loc[coin]['Balance']
    btc_bal=cpdf.loc[coin]['BTC_VAL']
    o_type=cpdf.loc[coin]['Type']  
    logging.warning("Auth Amnt for {} is {} and is holding {}".format(coin,auth_amt,btc_bal))
    buy_price=cur_price*1.0002
    max_buy_quant=(auth_amt-btc_bal)/buy_price 
    
    sell_price=round(cur_price*.997,8)
    max_sell_quant=round(((btc_bal-auth_amt)/sell_price),8)
    '''begin holding logic'''
    
    
    pp=JMDB.getPivotPoints(coin,period)

    
    if (o_type == 'sell') | (o_type == 'buy'):
        logging.warning("Awaiting open {} order.  Do not trade: {}".format(o_type,coin))
        return 0
    #search for buying position. 
    if btc_bal <= (auth_amt*.01):
        #Large purchases like these should buy between pivot points.  Sells, other than tstop, use PP also. set that up.             
        buy_quant=round(max_buy_quant*.8,8)
        total=round(buy_quant*buy_price,8) 
        if total <= .01:
            logging.warning("Way too small guy....grow some balls please.")            
            return 0
        elif (pp.pivotpoint[0] <= buy_price): 
            logging.warning("Price above pivot piont, wait for buy signal.")
        elif (pp.sup1[0] >= buy_price):
            logging.warning("BUY ZONE SUP1 ACTIVATED for {}!".format(coin))
            JMTB.buy(coin,buy_price,buy_quant)
            logging.warning("Buy {} of {} at {} for a total BTC Value of {}".format(buy_quant,coin,buy_price,total))
        elif (pp.pivotpoint[0] >= buy_price) & (pp.sup1[0] >= buy_price):
            logging.warning("No man's land.  Don't buy yet.")
        else:
            logging.warning("No conditions triggered for {}".format(coin))
        return 1
    elif btc_bal <= (auth_amt*.5):
        #Increment holding by looking for good relative price.
        buy_quant=round(max_buy_quant*.299,8)
        total=round(buy_quant*buy_price,8)
        if total <= .01: return 0
        elif (pp.pivotpoint[0] >= buy_price): 
            logging.warning("Price above pivot piont for {}, wait for buy signal.".format(coin))
        elif ((pp.pivotpoint[0]*.85) <= buy_price):
            logging.warning("BUY ZONE SUP1 ACTIVATED for {}.".format(coin))            
            logging.warning("Buy {} of {} at {} for a total BTC Value of {}".format(buy_quant,coin,buy_price,total))
            JMTB.buy(coin,buy_price,buy_quant)
        return 1
    elif (btc_bal > (auth_amt*.5)) & (btc_bal <= auth_amt):
        #As we get closer to auth amount, be more selective.
        buy_quant=round(max_buy_quant*.299,8)
        total=round(buy_quant*buy_price,8)
        if total <= .01: 
            logging.warning("Nope, {} isn't enough to warrent a trade!".format(coin))            
            return 0
        elif (pp.pivotpoint[0] <= buy_price): 
            logging.warning("{} price above pivot piont, wait for buy signal.".format(coin))
            logging.warning("Buy {} of {} at {} for a total BTC Value of {}".format(buy_quant,coin,buy_price,total))
        elif (pp.sup2[0] >= buy_price):
            logging.warning("BUY ZONE SUP1 ACTIVATED for {}!".format(coin))
            logging.warning("Buy {} of {} at {} for a total BTC Value of {}".format(buy_quant,coin,buy_price,total))
            JMTB.buy(coin,buy_price,buy_quant)
        else: logging.warning("{} did not meet any buy paramters, {} is current buy price {} is pivotpoint.".format(coin,buy_price,pp.pivotpoint[0]))
        return 1      
    #check for selling position
        
    elif btc_bal > round((auth_amt*1.05),8):
        total=round(max_sell_quant*sell_price,8)
        logging.warning("{} holding over authorized amount - looking to TAKE PROFIT SOON!!!!.".format(coin))
        if total <= .01:
            logging.warning("{} trade not valuable enough.  Wait for more upward price movement.".format(coin))            
            return 0
        elif (pp.res1[0] <= sell_price): 
            logging.warning("{}price above Resistance Point, sell activated.".format(coin))
            JMTB.sell(coin,sell_price,max_sell_quant)
            logging.warning("Sell{} {} at {} for a total BTC Value of: {}.".format(coin,max_sell_quant,sell_price,total))  
        elif (pp.pivotpoint[0] >= sell_price):
            logging.warning("{} price too low, wait to sell.".format(coin))

        return 1
    else: 
        logging.warning("{} holding current position.  No buys or sells detected.".format(coin))
        return 0
        
def checkPivotPoint(coin,period):
    #Build open order filter.  
    logging.warning( "Checking pivot point strategy for {}".format(coin))
    cpdf=JMDB.getCurrentPosDB()
    auth_amt=cpdf.loc[coin]['Auth_BTC']
    cur_price=cpdf.loc[coin]['Price']
    balance=cpdf.loc[coin]['Balance']
    btc_bal=cpdf.loc[coin]['BTC_VAL']
    o_type=cpdf.loc[coin]['Type']  
    pp=JMDB.getPivotPoints(coin,period)
    logging.warning("Auth Amnt for {} is {} and is trading PivotPoint {}".format(coin,auth_amt,btc_bal))
    buy_price=cur_price*1.0002
    max_buy_quant=(auth_amt-btc_bal)/buy_price
    half_buy_quant=round(max_buy_quant/2,8)
    buy_total=round(buy_price*max_buy_quant,8)   
    sell_price=round(cur_price*.997,8)
    max_sell_quant=round(((btc_bal-auth_amt)/sell_price),8)
    sell_total=round(sell_price*max_sell_quant,8)
    M1=round((pp.sup1[0]+pp.sup2[0])/2,8)
    M2=round((pp.sup1[0]+pp.pivotpoint[0])/2,8)
    M3=round((pp.res1[0]+pp.pivotpoint[0])/2,8)
    M4=round((pp.res1[0]+pp.res2[0])/2,8)
    #DO NOT ALLOW FOR MULTIPLES BUYS IN THE SAME PRICE ZONE.  
    if (pp.sup2[0] >= buy_price) & (buy_total > .01):
        logging.warning("Buy zone 2. ".format(coin))
        logging.warning("Buy {} Price: {} Quantity {}:".format(coin,buy_price,max_buy_quant))        
        JMTB.buy(coin,buy_price,max_buy_quant)
        return 1
    elif (pp.sup1[0]>= buy_price) & (round(buy_total/2,8) > .01) & (btc_bal <= .001):
        logging.warning("Buy zone 1. ".format(coin))
        logging.warning("Buy {} Price: {} Quantity {}:".format(coin,buy_price,half_buy_quant)) 
        JMTB.buy(coin,buy_price,half_buy_quant)
        return 1
    elif (pp.res1[0] <= sell_price) & (round(sell_total/4,8) > .01):
        logging.warning("Sell {} Price: {} Quantity {}:".format(coin,sell_price,round(max_sell_quant/4,8))) 
        JMTB.sell(coin,sell_price,round(max_sell_quant/4,8))
        return 1
    elif (pp.pivotpoint[0]<= sell_price) & (round(sell_total/2,8)>.01):
        logging.warning("Sell {} Price: {} Quantity {}:".format(coin,sell_price,round(max_sell_quant/2,8))) 
        JMTB.sell(coin,sell_price,round(max_sell_quant/2,8))
        return 1
    print "No Pivot Point trades ATT."
    return 0
        
    
    
    pp=JMDB.getPivotPoints(coin,period)
#print JMTI.currentIndicator('20SMA','ETH',240)>=JMTI.currentIndicator('Highest_High', 'ETH',240)          