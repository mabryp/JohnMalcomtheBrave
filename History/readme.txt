This folder is for historical reference.  No need to worry about it.  

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

The Strategies:
	Breakout:  The breakout strategy can be enabled by setting "enable_breakout" to 1.  Breakout will buy that coin when/if the current price sets a new 5 period high (Rob suggests a daily period for this).  Breakout will only sell if/when the coin hits its trailing stop (currently hard coded to 4%, will be configurable in the future).
	
	Hold:  The hold strategy is enabled by setting "enable_hold" to 1.  Hold will hold 'X"BTC worth of that coin.  It will only buy if/when the valuation of that coin is less than it's given amount.  For example, I set the bot to hold .25BTC of Litecoin.  It reaches out and buys .25BTC worth of litecoin.  Then, the price doesn't move much.  One day, the price of Litecoin plummets - this causes the valuation of LTC to drop below .25 - so the bot will buy more LTC. 
		
		Conversely, if the price of LTC rises then the total valuation of LTC held by JMTB will surpass its allotted amount to
		maintain.  
		
		In short: Hold will buy on downtrends to get good bargains; but will sell in stages during uptrends.  
		
	Swing:  This strategy is not implemented yet.  Comming soon.... but will try to identify trends and buy into up-trending coin. 

TODO:

-Further segregate buy/sell algorithms to allow for buying on one period and selling on another.  
-Get off of Sqlite which does not allow for multi-threading.
    -incorporate multi-threading
-Build out three primary strategies: Breakout, Swing, and Hold Position. 
-Add exception handling to public API calls to prevent exceptions during times of internet congestion.  
-Minimize Public API calls and Local Database read/write.  Cache data in memory, then write once?
 
