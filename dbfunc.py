# -*- coding: utf-8 -*-
import pandas as pd
import sqlite3
import logging
import time, datetime

conn = sqlite3.connect('db.live')
c = conn.cursor()
conn.row_factory = sqlite3.Row

def createDatabase():
    c.execute('CREATE TABLE IF NOT EXISTS current_position (coin TEXT UNIQUE, Price REAL, Balance REAL, BTC_VAL REAL,\
                                                            Auth_BTC REAL, USD_Val REAL, OpenO REAL, Period INTEGER,\
                                                            OOrder_USD REAL, Type TEXT, Last_Buy REAL, Trailing_Stop REAL,\
                                                            Last_Sell REAL)')
    return 1
                                                            
def createTradeTable(coin):
    sqlqry=('CREATE TABLE IF NOT EXISTS %s_Trade_History (orderNumber TEXT, date NUMERIC, type TEXT, open TEXT, rate REAL,\
                                                            amount REAL, total REAL, tradeID TEXT)'%(coin))
    c.execute(sqlqry)
    return 1    
    




def updateTradeTable(coin, ttype, rate, amount, df):
    logging.warning('updateTradeTable() initiated for{}'.format(coin))
    resultingTrades=df['resultingTrades']
    oNumber=str(df['orderNumber'])
    if resultingTrades:
        for trade in resultingTrades:
            sqlqry=('INSERT INTO %s_Trade_History (orderNumber) VALUES (%s)'%(coin, oNumber))
            logging.warning(sqlqry)
            c.execute(sqlqry)
            conn.commit()
            tradeID=trade['tradeID']
            rate=trade['rate']
            amount=trade['amount']
            date=time.time()
            total=trade['total']
            ttype_=trade['type']
            if ttype_=='buy': 
                ttype=1
            elif ttype == 'sell':
                ttype=-1
            table='%s_Trade_History'%(coin)
            params=(table,date,ttype,rate,amount,total,tradeID,oNumber)
            sqlqry=('UPDATE %s SET date = %s,type=%s,open=0,rate=%s,amount=%s,total=%s,tradeID=%s WHERE orderNumber=%s'%(params))
            logging.warning(sqlqry)            
            c.execute(sqlqry)
            conn.commit()
    elif not resultingTrades:
        sqlqry=('INSERT INTO %s_Trade_History (orderNumber) VALUES (%s)'%(coin, oNumber))
        logging.warning(sqlqry)
        c.execute(sqlqry)
        conn.commit()
        table="%s_Trade_History"%(coin)
        date=time.time()
        params=(table,date,ttype,rate,amount,amount*rate,oNumber)
        sqlqry=('UPDATE %s SET date = %s, type = %s, open = 1, rate = %s, amount = %s, total=%s WHERE orderNumber=%s'%(params))
        logging.warning("updateTradeTable() no resulting trades for {}.".format(coin))
        logging.warning(sqlqry)
        c.execute(sqlqry)
    
    
    conn.commit()

def updateCurrentPos(df):
#    This block is kept for historical reasons.  Can be removed in the future. 
#    c.execute('CREATE TABLE IF NOT EXISTS current_position (coin TEXT UNIQUE, Price REAL, Balance REAL, BTC_VAL REAL,\
#                                                            Auth_BTC REAL, USD_Val REAL, OpenO REAL, Period INTEGER,\
#                                                            OOrder_USD REAL, Type TEXT, Last_Buy REAL, Trailing_Stop REAL,\
#                                                            Last_Sell REAL)')
    
    for coin in df.index:
        c.execute('INSERT OR IGNORE INTO current_position (coin) VALUES (?)',(coin,))
        c.execute('UPDATE current_position SET Price = ?, Balance = ?, BTC_VAL = ?, Auth_BTC = ?, USD_Val = ?, Period = ?,\
                   OpenO = ?, OOrder_USD = ?, Type = ? WHERE coin = ?',\
                   (df.loc[coin].Price,df.loc[coin].Balance,df.loc[coin].BTC_Val,df.loc[coin].Auth_BTC,df.loc[coin].USD_Val,\
                    df.loc[coin].Period,df.loc[coin].OpenO,df.loc[coin].OO_USD,df.loc[coin].OO_Type,coin))
        
    conn.commit()
    return 1
def getTotalBalance():
#    This block is kept for historical reasons.  Can be removed in the future. 
#    c.execute('CREATE TABLE IF NOT EXISTS current_position (coin TEXT UNIQUE, Price REAL, Balance REAL, BTC_VAL REAL,\
#                                                            Auth_BTC REAL, USD_Val REAL, OpenO REAL, Period INTEGER,\
#                                                            OOrder_USD REAL, Type TEXT, Last_Buy REAL, Trailing_Stop REAL,\
#                                                            Last_Sell REAL)')
    data=getCurrentPosDB()
    total = data['BTC_VAL'].sum()
    return total
    
def updateTrailingStop(coin,new_ts):
   c.execute('UPDATE OR REPLACE current_position SET Trailing_Stop = ? WHERE coin = ?',(new_ts,coin))
   conn.commit()
   return 1
   
def writePivotPoints(df,coin,period):
    timestamp=time.time()
    table='BTC_'+coin+str(period)+"__Pivot__"
    sqlqry=('CREATE TABLE IF NOT EXISTS %s (date NUMERIC UNIQUE, pivotpoint REAL, res1 REAL, res2 REAL, sup1 REAL,sup2 REAL)'\
            %(table))
    c.execute(sqlqry)

    sqlqry=('INSERT INTO %s (date,pivotpoint,res1,res2,sup1,sup2) VALUES (%s,%s,%s,%s,%s,%s )'\
             %(table,timestamp,df['pp'],df['res1'],df['res2'],df['sup1'],df['sup2']))
    c.execute(sqlqry)
    conn.commit()
    return 1

def getPivotPoints(coin,period):
    table='BTC_'+coin+str(period)+"__Pivot__"
    sqlqry=('SELECT * FROM %s ORDER BY date DESC LIMIT 1'%(table))
    data=pd.read_sql(sqlqry,conn)
    return data
   
def getCurrentPosDB():
    sqlqry=('SELECT * FROM current_position')
    df=pd.read_sql(sqlqry,conn,index_col='coin')
    return df
    
def writeChartData(df, pair, period):
    df.set_index('date',inplace=True)
    df.to_sql(pair+str(period),conn,if_exists='replace')
    return 1
    
def readChartDate(coin,period):
    try:
        table='BTC_'+coin+str(period)
        sqlqry=('SELECT date FROM %s ORDER BY date DESC LIMIT 1'%(table))
        c.execute(sqlqry)
        return c.fetchall()
    except sqlite3.Error:
        logging.warning("No local data for {}....updating".format(coin))
        return 0

def readChartData(coin,period):
        table='BTC_'+coin+str(period)
        sqlqry=('SELECT * FROM %s'%(table))
        data= pd.read_sql(sqlqry,conn)
        return data

def getLastCandlestick(coin,period):
    table='BTC_'+coin+str(period)
    sqlqry=('SELECT * FROM %s ORDER BY date DESC LIMIT 1'%(table))
    data=pd.read_sql(sqlqry,conn)
    return data
    
def writeIndicators(df,coin,period):
    pair='BTC_'+coin
    df.set_index('date',inplace=True)
    df.to_sql(pair+str(period)+'__indicators_',conn,if_exists='replace')
    return 1
    
def returnIndicators(coin,period):
    table='BTC_'+coin+str(period)+'__indicators_'
    sqlqry=('SELECT * FROM %s ORDER BY date DESC LIMIT 1'%(table))
    data = pd.read_sql(sqlqry,conn)
    return data
    
    