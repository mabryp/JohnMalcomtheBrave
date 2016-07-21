John Malcom The Brave: Tilting Windmills 
Current Version: rc3.0.1
Release Date: 21JUL16

Description:

John Malcom The Brave provides a method of automating simple trading strategies with Poloniex.  The user is responsible to configuring trading logic and paramteters for the initiation of trades.  The functions are all described within the source-code and should provide for a simple interface.  


Theory of Operation:
tl;dr: JMTB operates through three primary phases:  
	
	Phase 1 - Data Accumulation: All public API queries happen here.  Data is stored to the local database.
		input: Public data calls
		output: Cached data in local database.

	Phase 2 - Analytics:  All calculations of indicators and trading logic happen here.
		input: Cached data in local database.
		output: Technical indicators and trading booleans saved to local database. 

	Phase 3 - Execution: Read the local database for trading booleans.  Execute trades identified in phase 2.
        input: Local database query.
        output: Executed trades and logs. 


JMTB keeps an updated database of all candlestick data for any given asset with any standard Poloniex time-period (5min, 15 min, 30min, 240min, 1440min).  By holding the data locally we can minimize the amount of dataqueries required to keep data in-sync.  JMTB then uses only locally stored data for all calculations and decisions.  Once these calculations and decisions have completed, those states are saved to the database as well.  Finally, the trading execution logic searches the database for all assets which qualify for trading.  With all trades identified, it then executes each trade as directed by the trading logic (again - this is passed thorugh the database).  

TODO:

-Further segregate buy/sell algorithms to allow for buying on one period and selling on another.  
-Get off of Sqlite which does not allow for multi-threading.
    -incorporate multi-threading
-Build out three primary strategies: Breakout, Swing, and Hold Position. 
-Add exception handling to public API calls to prevent exceptions during times of internet congestion.  
-Minimize Public API calls and Local Database read/write.  Cache data in memory, then write once?
 