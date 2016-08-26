This folder is for historical reference.  No need to worry about it.  

John Malcom The Brave: Tilting Windmills 
Current Version: rc4.0.1
Release Date: 21AUG16
UPDATE: AUG2016

The biggest changes here are mechanical in nature.  The way JMTB queried and processed data in the previous version was very easy to break.  This made adding new features very difficult.  In this version I've broken up functions in a more modular way.  This allowed me to clean up a great deal and add more flexibility.  Transitioning to a new database will be much easier now. The most important change is now he system can recieve custom strategies - if a person is willing to create them.  All the data, indicators, and filters are ready in the form of easy to use datatypes.  Anyone who wants a crash course in how to code new strategies can come by and we'll code a couple of simple strategies together and get you started.  Any strategy you write here will be able to transition with the code through it's upcoming changes, so any time you invest in a strategy will be respected (in other words I'll never make any changes which breaks your code - so you can build over time).    I hope you give it a shot, I think with your help we can make a pretty cool system.  

Backtesting:  I have not written anything for a backtesting system.  The backtesting feature will be the first part of the MYSql transition because it is required for the coin screener project.  I will get backtesting working on the new database, code the indicators, and also build the queries for the coin screener.  Then it is a simple manner of moving all of the non database code over the new backend.\

Website/Graphs:  My intention is to keep all outputs and data as text to STOUT or log-files.  Any websites or graphs will need to be written as different code altogether and use the database JMTB and Coin Screener will populate.       

Basic Roadmap going forward:
I will begin by working on MYSql and python.  I have not used mysql before, so there is going to be another learning curve.  I do not expect to learn sql in any huge way, but just enough to do what I need confidently.  I think my experience with SQLite has given me a nice test platform to prepare, and I think I can get what I need in a few weeks to no more than a couple months.  Once I've gotten that, we'll have a database of the candlestick data for every coin on poloniex.  When fully populated, and running, the database will have about 4.5 million entries and the public API calls will need to run as a service.  However, the screener function itself is going to be much less daunting and probably completed fairly quickly.

I have no hard timeline, but I'd really like to have the screener done by the time I go on vacation in November.  Inshala.   







Description:

John Malcom The Brave provides a method of automating simple trading strategies with Poloniex.  The user is responsible to configuring trading logic and paramteters for the initiation of trades.  The functions are all described within the source-code and should provide for a simple interface.  


Theory of Operation:
tl;dr: JMTB operates through three primary phases:  
	
	Phase 1 - Data Accumulation: All public API queries happen here.  Data is stored to the local database.
		input: Public data calls
		output: Cached data in local database.

	Phase 2 - Analytics:  All calculations of indicators and trading logic happen here.
		input: Cached data from local database.
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
		
	Pivot Poin: This strategy utilizes pivot points to buy at calculated support prices and sell at resistance points. 

TODO:
Pre-Todo
-Further segregate buy/sell algorithms to allow for buying on one period and selling on another. 
	*Not done, but buy/sell filters were worked out with Rob which make this feature less important.   
-Get off of Sqlite which does not allow for multi-threading.
    -incorporate multi-threading
	*Not done.  Implemented once, and realized it's not worth the complication at the moment.  
-Build out three primary strategies: Breakout, Swing, and Hold Position. 
	*Done, but swing has been replaced pivot_point
-Add exception handling to public API calls to prevent exceptions during times of internet congestion.  
	*Not done, didn't get around to it. 
-Minimize Public API calls and Local Database read/write.  Cache data in memory, then write once?
	*Done, but can be optimized more.  Decreased public calls by 90% with more relevant data. 

UPDATE 21AUG2016:
The next time this has a major upgrade it will be moved to the MySQL server. Below is a list of what I think should be worked on next - whenever that is. 
- Flesh out trade history tables and logic.  
- Flesh out open orders logic.  
- Most work will be handled after the coin-screener is working and outputing reports on the ALTCOIN market.  
