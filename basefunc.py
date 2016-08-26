# -*- coding: utf-8 -*-
import json
import urllib, urllib2
import hmac, hashlib
import time
import datetime
import pandas as pd
import yaml
import dbfunc as JMDB
import logging

def yaml_loader(filepath='config.yaml'):
    
    with open(filepath, "r") as file_descriptor:
        data = yaml.load(file_descriptor)
        return data
        
def api_query(command, req={},jsonV=0):
    #All authenticated queries will run through this function
    req['command'] = command
    req['nonce'] = int(time.time()*1000000000)
    post_data = urllib.urlencode(req)
    logging.warning("Query initiated with post code: {}".format(post_data))
    sign = hmac.new(secret, post_data, hashlib.sha512).hexdigest()
    headers = {'Sign': sign,'Key': key}
    ret = urllib2.urlopen(urllib2.Request('https://poloniex.com/tradingApi', post_data, headers))  
    if jsonV==0:                
        jsonRet = pd.read_json(ret, typ='dataframe', dtype=False)
        return jsonRet
    elif jsonV==1:
        jsonRet2 = json.load(ret)
        return jsonRet2

def getTicker():
        url = ('https://poloniex.com/public?command=returnTicker') 
        logging.warning('getTicker at {}'.format(url))
        ticdf = pd.DataFrame()
        ticker = pd.read_json(urllib2.urlopen(url)) 
        for alt in searchCoins:
            ticdf['Ticker:'+alt] = ticker['BTC_'+alt]
        ticdf['Ticker:BTC']=1
        ticdf.to_pickle('ticdf.pickle')
        return ticdf
        
def getBalance():
    balance = api_query('returnBalances')
    baldf = {}
    for alt in searchCoins:
        baldf[alt] = balance[alt]
    baldf['BTC']=balance.BTC
    return baldf
    
def getBTC_USD():
        #Pulls the CoinDesk Bitcoin Price Index
        url = 'https://api.coindesk.com/v1/bpi/currentprice/USD.json'
        logging.warning('Accessing BTC_USD..'+url)
        response = urllib2.urlopen(url)
        temp = pd.read_json(response)
        return temp['bpi']['USD']['rate_float']
        
def coinSettings(coin):
    with open('config.yaml', "r") as file_descriptor:
        data = yaml.load(file_descriptor)
    return data['coin'][coin]
    
def returnOpenOrders(full=0):
        odic={}
        data = api_query('returnOpenOrders', {"currencyPair":'all'},1 )
        for coin in searchCoins:
            odic[coin]=data['BTC_'+coin]            
        return odic

def getChartdata(pair, period_minutes):
                period_seconds=period_minutes*60
                start = int(time.time()-(period_seconds * 90))
                end = int(time.time())
                url = ('https://poloniex.com/public?command=returnChartData&currencyPair='+pair+'&start='+str(start)+'&end='+str(end)+'&period='+str(period_seconds))
                logging.warning("Updating Chart Data: "+url)
                response = urllib2.urlopen(url)
                chartData = pd.read_json(response)
                return chartData 

def splash():
    data = yaml_loader() 
    breakout_budget=data['strat_budget']['breakout_budget']
    pp_budget=data['strat_budget']['pivot_budget']
    hold_pos_quant = round(JMDB.getTotalBalance() - (pp_budget + breakout_budget), 8)
    logging.warning('*** Accumulator Budget: {}, Pivot_Point Budget: {}, Breakout Budget: {}'.format(hold_pos_quant,pp_budget,breakout_budget))
    holdpos=[]
    breakout=[]
    pivot=[]
    for coin in searchCoins:
        if data['coin'][coin]['enable_breakout'] == 1:
            breakout.append(coin)
        elif data['coin'][coin]['enable_hold_pos'] == 1:
            holdpos.append(coin)
        elif data['coin'][coin]['enable_pivot'] == 1:
            pivot.append(coin)
    logging.warning("##### Coins trading Accumulator: {}".format(str(holdpos)))
    logging.warning("******Coins trading Breakout: {}".format(breakout))
    logging.warning("^^^^^ Coins trading Pivot: {}".format(pivot))
    
    time.sleep(.2)
      
def snapshot(dftic, dicbal, dicord):
    snapshot = pd.DataFrame(index=searchCoins)
    USD = getBTC_USD()
    data = yaml_loader() 
    pp_budget=data['strat_budget']['pivot_budget']
    breakout_budget=data['strat_budget']['breakout_budget']
    hold_pos_quant = round(JMDB.getTotalBalance() - (pp_budget + breakout_budget), 8)
    logging.warning('*** Accumulator Budget: {}, Pivot Point Budget: {}, Breakout Budget: {}'.format(hold_pos_quant,pp_budget,breakout_budget))
    for key in dicbal:
        
        if key == 'BTC':
            last_=round(dftic['Ticker:'+key]['last'],9)
            bal = float(dicbal[key])
            auth_btc=bal
            usd_val=USD*bal
            btcval=bal
            period=0
            typo,openo,openov = 'None',0,0
        elif key != 'BTC':
            stt = coinSettings(key)
            coin_quant = stt['auth_amt']
            if stt['enable_hold_pos'] == 1:
                auth_btc=hold_pos_quant * coin_quant
            elif stt['enable_breakout']== 1:
                auth_btc=breakout_budget * coin_quant
            elif stt['enable_pivot'] == 1:
                auth_btc=pp_budget * coin_quant
            last_=round(dftic['Ticker:'+key]['last'],9)
            bal = float(dicbal[key])
            btcval=last_*bal
            usd_val=USD*btcval
            oo=dicord[key]
            openov, openo,typo=0,0,'None' 
            period = stt['period']
            for i in oo:
                typo,rateo,amnto = i['type'],i['amount'],i['rate']
                oval=float(rateo)*float(amnto)
                openov = USD*oval
                openo += 1                
        snapshot.set_value(key, 'Price', last_)
        snapshot.set_value(key, 'Balance', bal)
        snapshot.set_value(key, 'BTC_Val', btcval)
        snapshot.set_value(key, 'Auth_BTC', auth_btc)
        snapshot.set_value(key, 'USD_Val', usd_val)
        snapshot.set_value(key, 'Period', period)
        snapshot.set_value(key, 'OpenO', openo)
        snapshot.set_value(key, 'OO_USD', openov)
        snapshot.set_value(key, 'OO_Type', typo)
        
    return snapshot
    
def updateChartData(coin, period):
    JMDB.writeChartData(getChartdata('BTC_'+coin, period),'BTC_'+coin,period)
    return 1    

#def HandleOpenOrders(coin,trade,price,quantity):
#    oodic=JMTB.returnOpenOrders()
#    if not oodic[coin] : return 0
#    if trade=='buy':
#        print "Compare buy orders!"
#        old_price=oodic[coin][0]['rate']
#        old_amnt=oodic[coin][0]['amount']
#        old_type=oodic[coin][0]['type']
#        old_date=oodic[coin][0]['date']
#        ordernumber=oodic[coin][0]['orderNumber']
#        if old_price > round(price*1.005,8): 
#            print "Cancel ",ordernumber
#            data = JMTB.api_query('cancelOrder', {"orderNumber":str(ordernumber)},1 )
#            print data
#            return 1
#        elif old_price < price:
#            print "Hold ", ordernumber
#        
#        
#
#    
#    
#HandleOpenOrders('DASH','buy',.019,4)


def syncChartData(coin, period):
#Return 1 if updated, 0 if not.  No need to update indicators if 0 is returned. 
        seconds = period*60        
        candle_stamp=JMDB.readChartDate(coin,period)
        if not candle_stamp: 
            updateChartData(coin,period)
            candle_stamp=JMDB.readChartDate(coin,period)
            return 1
        diff = (datetime.datetime.utcnow() - (datetime.datetime.strptime(candle_stamp[0][0], '%Y-%m-%d %H:%M:%S')))
        diffs_ = datetime.timedelta.total_seconds(diff)         
        if int(diffs_) > seconds:
            logging.warning("Chart data for: "+coin+" NOT in sync.  Different by: "+str(int(diffs_))+" most recent data from: "\
                   +candle_stamp[0][0])
            updateChartData(coin,period)
            time.sleep(1)
            return 1
        elif seconds >= int(diffs_): 
            logging.warning("{} with period: {} is in sync.".format(coin,period))
            logging.warning("Next refresh in: {} minutes".format(int(seconds-diffs_)/60))
            return 0
                     
    #            time.sleep(2)  

def testTrade(coin):
    cpdf=JMDB.getCurrentPosDB()
    price=cpdf.loc[coin]['Price']
    buy_price=round(price*1.01,8)
    sell_price=round(price*.99,8)
    buy_amnt=round(0.012/buy_price,8)
    sell_amnt=round(0.012/sell_price,8)
    btc_val=cpdf.loc[coin]['BTC_VAL']
    if btc_val <= .1:
        print "Test Buy of {} {} at price {}".format(coin,buy_amnt,buy_price)
        buy(coin,buy_price,buy_amnt)
        return 1
    if btc_val >= .1:
        print "Test Sell of {} {} at price {}".format(coin,sell_amnt,sell_price)
        sell(coin,sell_price,sell_amnt)
        return 1
    

def sell(coin,sell_rate,sell_amnt):
    if sell_rate*sell_amnt < .01:
        print "Trade discarded locally, trade value must exceed .01BTC."        
        return 0
    sell_Response = api_query('sell',{"currencyPair":"BTC_"+coin,"rate":sell_rate,"amount":sell_amnt})
    log = open('tradehist.log', 'a')
    log.write("***\n"+str(datetime.datetime.utcnow())+"\nSELL: "+coin+" QUANTITY: "+str(sell_amnt)+" RATE: "+str(sell_rate)+".\n")
    #JMDB.updateTradeTable(coin,-1,sell_amnt,sell_rate,sell_Response)
    logging.warning('Sell: {} Quantity: {} Rate: {}'.format(coin,sell_amnt,sell_rate))
    for entry in sell_Response:
        print entry    
        log.write(str(sell_Response))
        log.write(str(entry))
    log.write("\t**********\n\n")
    log.close()                
    return 1

def buy(coin,buy_rate,buy_amnt):
    #This is where the Last_Buy price is added to the current_position table. 
    if buy_rate*buy_amnt < .01:
        print "Trade discarded locally, trade value must exceed .01BTC."
        return 0
    data=coinSettings(coin)
    t_settings=data['trailing_stop']
    t_set=1-t_settings     
    t_stop = buy_rate*t_set
    JMDB.updateTrailingStop(coin,t_stop)
    buy_Response = api_query('buy',{"currencyPair":"BTC_"+coin,"rate":buy_rate,"amount":buy_amnt})
    log = open('tradehist.log', 'a')
    log.write("***\n"+str(datetime.datetime.utcnow())+"\nBUY: "+coin+" QUANTITY: "+str(buy_amnt)+" RATE: "+str(buy_rate)+".\n")
    #JMDB.updateTradeTable(coin, 1, buy_rate, buy_amnt, buy_Response)
    logging.warning('Buy: {} Quantity: {} Rate: {}'.format(coin,buy_amnt,buy_rate))    
    for entry in buy_Response:
        print entry
        log.write(str(buy_Response)) 
        log.write(str(entry))
    log.write("\t**********\n\n")
    log.close()
    return 1
                     
file_path = 'config.yaml'
data = yaml_loader(file_path) 
searchCoins = data['searchCoins']
key = data['Auth']['key']
secret = data['Auth']['secret'] 