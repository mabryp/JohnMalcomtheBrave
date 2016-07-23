# -*- coding: utf-8 -*-
"""
Created on Fri Jul 08 15:27:34 2016
Check the readme for more information.  Edit the config.yaml file to configure settings and assets.
@author: Phill
"""
import random
import json
import smtplib
import urllib, urllib2
import hmac, hashlib
import time
import datetime
import pandas as pd
import sqlite3
import yaml 

'''-------------------API QUERY Function-------------------------------'''
def api_query(command, req={},jsonV=0):
    #All authenticated queries will run through this function
    req['command'] = command
    req['nonce'] = int(time.time()*1000000000)
    post_data = urllib.urlencode(req)
    print "\n\t\tQuery initiated with post code: "+post_data+str(datetime.datetime.utcnow())
    sign = hmac.new(secret, post_data, hashlib.sha512).hexdigest()
    headers = {'Sign': sign,'Key': key}
    ret = urllib2.urlopen(urllib2.Request('https://poloniex.com/tradingApi', post_data, headers))  
    if jsonV==0:                
        jsonRet = pd.read_json(ret, typ='dataframe', dtype=False)
        return jsonRet
    elif jsonV==1:
        jsonRet2 = json.load(ret)
        return jsonRet2
    
def yaml_loader():    
    with open('config.yaml', "r") as file_descriptor:
        data = yaml.load(file_descriptor)
        return data
def getmsg():
    with open('msg.yaml', 'r') as strings:
        data = yaml.load(strings)
        return data 
        
def coinSettings(coin):
    yaml_loader()
    data = yaml_loader()     
    return data['coin'][coin]
    
def getPeriod(coin):
    data = yaml_loader()
    data_ = data['coin'][coin]
    return data_['period']


def banner():
    num=random.randrange(1,16,1)
    msg = getmsg()
    remark= msg['msg']['killroy'][num]
    try:    
        print "\n"+"*"*200
        print "\t\t\t\t\t¯\_(ツ)_/¯ - "+remark
        print "*"*200
    except UnicodeDecodeError:
        print "\n"+"*"*200
        print "\t\t\t\t\t¯\_(ツ)_/¯ - This is an honest error and I have no idea why!"
        print "*"*200
    
    
def getTradeHist(pair, period, year=2016,month=1,day=1):
    begin = datetime.date(year, month, day)
    start = time.mktime(begin.timetuple())
    end = time.time()
    hist = api_query('returnTradeHistory', {'currencyPair':pair, 'start':str(start),'end':str(end)},1)
    df = pd.DataFrame(hist)
    if df.empty:
        return 0
    elif not df.empty:
        df.set_index('date',inplace=True)
        df['rate'] = df.rate.astype(float)
        df['amount'] = df.amount.astype(float)
        df['fee'] = df.fee.astype(float)
        df['total'] = df.total.astype(float)
        table=str(pair)+str(period)
        df.to_sql(table+'_trade_hist', conn,if_exists='replace')
        conn.commit()
        #print df.head()
          
    table = pair+str(period)
    sqlqry = ('SELECT * FROM %s_trade_hist'%(table))
    df = pd.read_sql(sqlqry,conn)
    buydf = df.loc[df.type == 'buy']
    selldf = df.loc[df.type == 'sell']
    df.sort('date',ascending=True,inplace=True)
    print "\n"+"*"*15+"SUMMARY FOR : "+pair
    print pair+" average price paid: "+str(buydf.rate.mean())
    print pair+" average sold price: "+str(selldf.rate.mean())
    print pair+" maximum price paid: "+str(buydf.rate.max())
    print pair+" maximum price sold: "+str(selldf.rate.max())
    print pair+" average buy quantity: "+str(buydf.amount.mean())
    print pair+" average sell quantity: "+str(selldf.amount.mean())
    print "*"*50   
    
def checkUpdate(pair, period):
    coin = pair.replace("BTC_","")
    data = coinSettings(coin)
    auth_btc = data['auth_amt']
    seconds = period * 60
    
    def Update_Chart_table(pair, period):
            def getChartdata(pair='BTC_ETH', period_minutes = 15):
                period_seconds=period_minutes*60
                start = int(time.time()-(period_seconds * 100))
                end = int(time.time())
                url = ('https://poloniex.com/public?command=returnChartData&currencyPair='+pair+'&start='+str(start)+'&end='+str(end)+'&period='+str(period_seconds))
                print "\n"+url+"\n"
                response = urllib2.urlopen(url)
                chartData = pd.read_json(response)
                return chartData       
            '''Query Candlestick data for any coin and update the DATABASE table for BTC_coinYYY (period)'''
            table = str(pair)+str(period)
            data = getChartdata(pair,period)
            data.set_index('date',inplace=True)
            data.to_sql(str(table),conn,if_exists='replace') 
            return
            
    qry ='CREATE TABLE IF NOT EXISTS %s (date NUMERIC UNIQUE, close REAL, high REAL, low REAL, open REAL, quoteVolume REAL, volume REAL, weightedAverage REAL) ' %(pair+str(period))
    c.execute(qry)    
    c.execute("UPDATE OR IGNORE current_position SET Auth_BTC_Value = ? WHERE coin = ?",(auth_btc, coin))
    print "\n*Checking Chart Data :"+pair+" with period: "+str(period)   
    sqlqry = 'SELECT date from '+pair+str(period)+' ORDER BY date DESC LIMIT 1'   
    c.execute(sqlqry)
    df = c.fetchall()
    
    if not df:
        print "Local cache for: "+pair+" "+str(period)+": NOT CACHED: Accessing most recent candlestick data.\n"
        Update_Chart_table(pair, period)
    else:
        candle_stamp = df[0]
        print "Chart Data time: "+candle_stamp[0]
        print "Current Time   : "+str(datetime.datetime.utcnow())
        diff = (datetime.datetime.utcnow() - (datetime.datetime.strptime(candle_stamp[0], '%Y-%m-%d %H:%M:%S')))
        diffs_ = datetime.timedelta.total_seconds(diff)
        if diffs_ > seconds:
            Update_Chart_table(pair, period)
            print "Updating chart data for "+pair
            return 1
        else: print "Most recent data cached."
        return 0

def getBTC():
        
    def getBalance(coin):
        balance = api_query('returnBalances')
        print coin+" balance: "+balance[coin]
        return balance[coin]
    
    def getBTC_USD():
        #Pulls the CoinDesk Bitcoin Price Index
        url = 'https://api.coindesk.com/v1/bpi/currentprice/USD.json'
        response = urllib2.urlopen(url)
        temp = pd.read_json(response)
        return temp['bpi']['USD']['rate_float']
        
    c.execute('CREATE TABLE IF NOT EXISTS current_position (coin TEXT UNIQUE, price REAL, quantity REAL, BTC_Val REAL, Auth_BTC_Value REAL, USD REAL, open_orders INTEGER, Last_Buy REAL, Trailing_Stop REAL, Last_Sell REAL)')   
    btc_bal = getBalance('BTC')
    USD = getBTC_USD()
    btc_holding =   float(btc_bal)*float(USD)  
    c.execute("INSERT OR IGNORE INTO current_position (coin) VALUES ('BTC')")  
    c.execute("UPDATE current_position SET price = 1, quantity = ?, USD = ? WHERE coin = 'BTC'",(btc_bal,btc_holding))
   
def updateCurrent_Position(coin):
    
    
    def getBalance(coin):
        balance = api_query('returnBalances')
        print coin+" balance: "+balance[coin]
        return balance[coin]
    
    def getBTC_USD():
        #Pulls the CoinDesk Bitcoin Price Index
        url = 'https://api.coindesk.com/v1/bpi/currentprice/USD.json'
        response = urllib2.urlopen(url)
        temp = pd.read_json(response)
        return temp['bpi']['USD']['rate_float']
    
       
    def getTicker(coin):
        url = ('https://poloniex.com/public?command=returnTicker')
        ticker = pd.read_json(urllib2.urlopen(url)) 
        return ticker[coin]    
    
    def returnOpenOrders(pair):
        data = api_query('returnOpenOrders', {"currencyPair":'all'} )
        
        return data[pair]

    quantity=getBalance(coin)
    last = getTicker('BTC_'+coin)
    last = last['last'] 
    USD = getBTC_USD()
   
    btc_val = float(quantity) * last
    usd_val = btc_val * USD
   
    openOrders = returnOpenOrders("BTC_"+coin)
    #Create a simple function which will iterate through the open-orders reply, grab the date and then cancel the order 
    #if it is over X periods old.  Perhaps this can be configurable - how long do you want to hold open orders? How many orders at once?
    if openOrders:
        orders = 0
        placeHolder = []
        for orders_ in openOrders:
            print orders_
            orders += 1 
            placeHolder.append(orders_)            
            period_ = getPeriod(coin)        
            orderNumber = placeHolder[0]['orderNumber']
            date = placeHolder[0]['date']
            offset = (period_*2)*60
            diff = (datetime.datetime.utcnow() - (datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')))
            diffs_ = datetime.timedelta.total_seconds(diff)
            if diffs_ > offset:
                print "Cancel the order number: "+str(orderNumber)
                cancel_o = api_query('cancelOrder', {"orderNumber":str(orderNumber)})
                print str(cancel_o)+" canceled order number: "+str(orderNumber)
            else:
                print "\nDo not cancel any orders: "
            

        with open('open_orders.log', 'a') as outfile:
            outfile.write(str(placeHolder[0]))    
    else: 
        orders = 0
    
    c.execute('INSERT OR IGNORE INTO current_position (coin) VALUES (?)',(coin,))    
    c.execute('UPDATE current_position SET coin = ?, price = ?, quantity = ? , USD = ?, open_orders = ?, BTC_Val = ? WHERE coin = ?',(coin,last,quantity,usd_val,orders,btc_val,coin))
    
    #c.execute('UPDATE current_position set open_orders = ? WHERE coin = ?',(btc_val,coin))
    conn.commit
    return 1
   
def setIndicators(pair, period):  
    '''Pulls its data from the most recent data available on the database.  make sure to update the database. '''
    
    def getData(pair, period, columns="date, close"):
        ''' Enter the columns you want in a pandas format. Defaults to date-time and close columns.''' 
        
        
        
        
        table = pair+period
        dataframe_ = pd.read_sql('SELECT '+columns+' FROM '+table, conn,index_col = 'date')
        return dataframe_
        
    SMA = getData(pair, period, columns='date, close, high, low')    
    SMA['20SMA']=SMA.close.rolling(window=20,center=False).mean()
    SMA['30SMA']= SMA['close'].rolling(window=30,center=False).mean()
    SMA['BB_UP']= SMA['close'].rolling(window=20,center=False).mean() + (SMA['close'].rolling(min_periods=20,window=20,center=False).std()* 2)
    SMA['BB_LWR']= SMA['close'].rolling(window=20,center=False).mean() - (SMA['close'].rolling(min_periods=20,window=20,center=False).std()* 2)
    SMA['Highest_High']= SMA['high'].rolling(window=5,center=False).max()
    SMA['Lowest_Low'] = SMA['low'].rolling(window=5,center=False).min()
    SMA.to_sql(pair+'__indicators__'+period, conn, if_exists='replace')
    return 1
    
def setTrailingStop(pair):
    coin = pair.replace("BTC_","")
    c.execute("SELECT * FROM current_position WHERE coin = ?",(coin,))
    data = c.fetchall()
    current_price = data[0][1]
    new_t_stop = current_price *.96
    old_t_stop = data[0][8]
    if old_t_stop:     
        if new_t_stop >= old_t_stop*1.02:
            c.execute("UPDATE OR REPLACE current_position SET Trailing_Stop = ? WHERE coin = ?",(new_t_stop, coin))
            print "New Trailing Stop for :"+coin+", "+str(new_t_stop)
        elif old_t_stop > new_t_stop:
            print "Discarded T_Stop: "+str(new_t_stop)+";  Current T_Stop: "+str(old_t_stop)
            pass
    elif not old_t_stop:
        c.execute("UPDATE OR REPLACE current_position SET Trailing_Stop = ? WHERE coin = ?",(new_t_stop, coin))
        print "New Trailing Stop for :"+coin+", "+str(new_t_stop)
    conn.commit()
    return 
    
def setTradeBoolean(pair, period):
    
    sqlqry = "SELECT * from "+pair+"__indicators__"+str(period)
    data_ = pd.read_sql(sqlqry,conn)
    data_ = data_.iloc[-2:]
    data_['P_Over_20MA']= data_.close > data_['20SMA']
    data_['P_Over_30MA']= data_.close > data_['30SMA']
    data_['BB_Top_Break'] = data_.close >= data_.BB_UP
    data_['BB_Bottom_Drop'] = data_.close <= data_.BB_LWR
    data_['Buy_Small'] = data_.BB_Top_Break 
    data_['Sell_All'] = data_.BB_Bottom_Drop 
    data_['Breakout_High'] = data_.Highest_High <= data_.close
    data_['Breakout_Low'] = data_.Lowest_Low >= data_.close
    data_.to_sql(pair+'__boolean__'+str(period), conn, if_exists='replace')
    return 1
    
def initiateTradeSequence(coin, period):
    data = yaml_loader()
    sqlqry = "SELECT * from BTC_"+coin+"__boolean__"+str(period)
    data_ = pd.read_sql(sqlqry, conn)
    c.execute('SELECT * from current_position WHERE coin = ?',(coin,))
    current_ = c.fetchall()
    quantity_owned = current_[0][2]
    auth_budget = current_[0][4]
    price = current_[0][1] * .99
    max_sell = quantity_owned 
    min_sell = quantity_owned * .334
    if auth_budget != None:
        max_trade = (auth_budget / price) - quantity_owned
        min_trade = max_trade * .334
        micro_buy = max_trade * .1
    else: 
        print "Auth_Budget for "+coin+" is None"
        max_trade = 0
        min_trade = 0
        micro_buy = 0
        pass
    #Trailing stop checked first.  Will sell all if Trailing_Stop is hit.      
    if current_[0][1] <= current_[0][8]:
        print "Trailing Stop activated for: "+coin+"\n"
        print"last_trade: "+str(price)+", quantity_owned: "+str(quantity_owned)+", max_trade: "+str(max_trade)
        sell(coin,price,max_sell) 
        
    #Begin Breakout Strategy:    
    if data['coin'][coin]['enable_breakout'] == 1:
        print coin+" is trading with the Breakout Strategy!\n"
        #Begin trading sequence.  Every 'if' and 'elif' is the trading logic which checks for buy/sell operators.  
        #These operators are set in the function setTradeBoolean()
        #
        #Three types of breakouts: Buy_Small, Micro_Buy, and Max_Buy.
            #Buy_Small will buy 33% of its alloted ammount when Price hits top BB Band.
            #Micro_Buy will buy 10% of its alloted ammount when price breaks above 20MA and 30MA
            #Max_Buy will buy full alloted amount when price hits new five-day high. 
        if data_.iloc[-1]['Breakout_High'] & (current_[0][6] <= 2):
            print data_.iloc[-1]
            print "\nBreakout for :"+coin
            print"last_trade: "+str(price)+", quantity_owned: "+str(quantity_owned)+", max_trade: "+str(max_trade)
            buy(coin,price,max_trade)
       
       
        elif data_.iloc[-1]['Buy_Small'] & ( current_[0][6] <= 2 ) & (price*min_trade > .001): 
            print data_.iloc[-1]
            print "\nBuy Small for "+coin
            print"last_trade: "+str(price)+", quantity_owned: "+str(quantity_owned)+", max_trade: "+str(max_trade)
            buy(coin,price,min_trade)
            
        elif (data_.iloc[-1]['P_Over_30MA'] & data_.iloc[-1]['P_Over_20MA']) & (current_[0][6] <= 2) & (price*micro_buy > .001):
            print data_.iloc[-1]
            print "\nMicro-Buy for "+coin
            buy(coin,price,micro_buy)
        
       

    #Begin Hold Position Strategy:
    elif data['coin'][coin]['enable_hold_pos'] == 1:
        print '\t'+coin+" is trading on a hold strategy!"
        if (current_[0][4] >= current_[0][3]) & (current_[0][6] <= 1) & (price*min_trade > .001):
            quant = ((auth_budget - current_[0][3])/price)*.8
            if quant*price >= .001: buy(coin,price,quant)
        elif (current_[0][4] <= current_[0][3]) & (data_.iloc[-1]['P_Over_20MA']) & (current_[0][6] <= 1) & (price*min_trade > .001):
            quant = ((current_[0][3] - auth_budget)/price)*.9
            if quant*price>=.001: sell(coin,price,quant) 
       
    #Begin swing strategy:        
    elif data['coin'][coin]['enable_swing']  == 1:
        print "\n\tYou must create a Swing strategy!\n"
       
        
def buy(coin,buy_rate,buy_amnt):
    #This is where the Last_Buy price is added to the current_position table. 
    t_stop = buy_rate*.96
    c.execute("UPDATE OR REPLACE current_position SET Last_Buy = ?, Trailing_Stop = ? WHERE coin = ?", (buy_rate, t_stop, coin))
    buy_Response = api_query('buy',{"currencyPair":"BTC_"+coin,"rate":buy_rate,"amount":buy_amnt})
    for entry in buy_Response:
        print entry
        log = open('tradehist.log', 'a')
        log.write("**********\n\nBought "+str(buy_amnt)+" of "+coin+" at price"+str(buy_rate)+".\n")
        log.write(str(buy_Response)) 
        log.write(str(entry))
        log.write("\n**********\n\n")
        log.close()
        content =  "Buy: "+coin+"\n"+str(buy_Response)+"\n"+str(entry)
        sendEmail(content)
        conn.commit() 
    
        
def sell(coin,sell_rate,sell_amnt):
    c.execute("UPDATE current_position SET Last_Sell = ? WHERE coin = ?", (sell_rate, coin))
    sell_Response = api_query('sell',{"currencyPair":"BTC_"+coin,"rate":sell_rate,"amount":sell_amnt})
    for entry in sell_Response:
        print entry    
        log = open('tradehist.log.txt', 'a')
        log.write("**********\n\nI have too much "+coin+" and I should sell at least "+str(sell_amnt)+" "+coin+".\n")
        log.write(str(sell_Response))
        log.write(str(entry))
        log.write("\n**********\n\n")
        log.close()                
        content = ("\n\nSold  "+coin+", Quantity: "+str(sell_amnt)+" "+coin+'\n'+str(sell_Response))
        sendEmail(content)
        conn.commit() 
        
def sendEmail(contents):
    try:
        data = yaml_loader()
        login = data['eMail']['uName']
        keyw = data['eMail']['auth']
        send_ = data['eMail']['sendTo']
        mail = smtplib.SMTP('smtp.gmail.com',587)
        mail.ehlo()
        mail.starttls()
        SND_MSG = ("Do not reply to this email.  It goes unchecked.\n" + contents)
        mail.login(login,keyw)
        mail.sendmail(login,send_,SND_MSG)
    except smtplib.SMTPException:
        print "Error: Unable to send email"  
        
    
'''Begin Global Variables and main()'''

_coin = yaml_loader()
searchCoins = _coin['searchCoins']

key = _coin['Auth']['key']
secret = _coin['Auth']['secret'] 

dbfile = _coin['Database']['file']


conn = sqlite3.connect(dbfile)
c = conn.cursor()
conn.row_factory = sqlite3.Row 
     

   


def main():
    getBTC()
    banner()

    for alt in searchCoins:
        period = getPeriod(alt)
        pair = 'BTC_'+ alt        
        print "\t\t\t\t\t|_______ "+pair+": "+str(period)+"_Begin_________|\n"        
        checkUpdate(pair, period) 
        updateCurrent_Position(alt)
        setTrailingStop(pair)              
        setIndicators(pair, str(period))       
        setTradeBoolean(pair, period)
        initiateTradeSequence(alt, period)
        updateCurrent_Position(alt)
        setTrailingStop(pair)     
        getTradeHist(pair, period)                
        print '\n\n'+"\t\t\t\t\t!!!!!!!!!!"+pair+": "+str(period)+"_Complete!!!!!!!!!!" 

        banner()
    
    return "Full cyle completed at: "+str(datetime.datetime.utcnow())

        
if __name__ == '__main__':
    print "\n\n"+main()     
    x = _coin['System']['Num_of_Cycles']
    while x >= 1:
        sleep = _coin['System']['Pause_Duration']
        y = _coin['System']['bind_loop']
        x -= y 
        print str(sleep)+" seconds between cycles. Started at: "+str(datetime.datetime.utcnow() )
        time.sleep(sleep)
        main()

conn.commit()   
c.close()
conn.close()
