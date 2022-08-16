
This is a spin-off of the Crypto-Gnome Bot Modded to work for me and my Strategy on Tradingview. <br >(original bot here https://github.com/CryptoGnome/Tradingview-Webhook-Bot)

This is a tradingview webhook  designed to be free & open source.  This bot is written using Python & Flask and is designed to run a free heroku server. It will allow you to create custom alerts in tradingview and send them to your own private webhook server that can place trades on your account via the api.

#### Support can be requested in our Discord:

# How to Webhook Server on Heroku

1.) Clone Project to Desktop

2.) [Create Free Heroku Account](https://www.heroku.com/)

3.) Edit config.json to add your own api keys & add a custom key to protect the server.

```You need to creat new keys on Bybit & give them the correct acess to trade and see token balance```
	
4.) Open a terminal in the cloned directory:

5.) Install Heroku CLI so you can work connect you your webserver.

https://cli-assets.heroku.com/heroku-x64.exe


6.) Submit the following lines into the terminal and press ENTER after each one to procces the code: 
 
 
``git init``

``heroku login``

``heroku create --region eu tv-trader-yourservernamehere``

``git add .``

``git commit -m "Initial Commit"``

``git push heroku master``


***Anytime you need to make a change to the code or the API keys, you can push a new build to Heroku:***

``git add .``

``git commit -m "Update"``

``git push heroku master``

# How to send alerts from TradingView to your new Webserver

After starting you server, you shoudl see an address that will allow you to access it like below:<br >

[https://YOUR_BOT_NAME.herokuapp.com/byit]

_Now when your alerts fire off they should go strait to your server and get proccessed on the exchange almost instantly!_

Right Now There are 2 Modes<br >
Genie - For GENIE Entries - Currently ONLY Supports 1 Entry at a time. <br >
Lambo - For LamboModd Strategy<br >
Davidd - For Davidd.tech Strategy

# TradingView Alerts Format 

-- Exit Long / Short ANY Strategy
```
{
	"key": "12345",
	"exchange": "#exchange#",
	"symbol": "#symbol#",
	"close_position": "True",
    	"close_pos_pct": "#close_pct#", -- Optional
	"cancel_orders": "True"

}
```
-- LamboModd Strategy
```
{
    "key": "12345",
    "order_mode": "Lambo",
    "exchange": "#exchange#",
    "symbol": "#symbol#",
    "cancel_orders": "True",
    "type": "Market",
    "time_in_force": "GoodTillCancel", ## GoodTillCancel, ImmediateOrCancel, FillOrKill, PostOnly
    "entry_side": "#entry_side#",
    "exit_side": "#exit_side#",
    "risk_pct": "#risk_pct#",
    "leverage": "#leverage#",
    "entry_price": "#close#", 
    "tp1_price": "#tp1_price#",
    "tp2_price": "#tp2_price#",
    "tp3_price": "#tp3_price#",
    "tp4_price": "#tp4_price#",
    "tp1_pos_pct": "#tp1_pos_pct#",
    "tp2_pos_pct": "#tp2_pos_pct#",
    "tp3_pos_pct": "#tp3_pos_pct#",
    "tp4_pos_pct": "#tp4_pos_pct#",
    "sl_price": "#sl_price#"
} 
```
```
{
    "key": "12345", - Coming Soon
    "order_mode": "Genie",
    "exchange": "#exchange#",
    "symbol": "#symbol#",
    "type": "Market",
    "entry_side": "Buy",
    "risk_pct": "5",
    "leverage": "2",
    "entry_price": "{{close}}"
}
```
```
{
	"key": "12345",
	"exchange": "#exchange#",
	"symbol": "#symbol#",
	"close_position": "True",
	"cancel_orders": "True"

}
```
-- Long Entry Davidd.tech Strategy
```
{
    "key": "12345",
    "order_mode": "Davidd",
    "exchange": "#exchange#",
    "symbol": "#symbol#",
    "cancel_orders": "True",
    "type": "Market",
    "entry_side": "#side#",
    "risk_pct": "5",
    "leverage": "2",
    "entry_price": "#close#", 
    "tp1_price": "#LongTP1#",
    "tp2_price": "#LongTP2#",
    "tp3_price": "#LongTPFULL#",
    "tp1_pos_pct": "#TakeAmount1#",
    "tp2_pos_pct": "#TakeAmount2#",
    "tp3_pos_pct": "100",
    "sl_price": "#LongSL#"
}
```
-- Short Davidd.tech Strategy
```
{
    "key": "12345",
    "order_mode": "Davidd",
    "exchange": "#exchange#",
    "symbol": "#symbol#",
    "cancel_orders": "True",
    "type": "Market",
    "entry_side": "#side#",
    "risk_pct": "5",
    "leverage": "2",
    "entry_price": "#close#", 
    "tp1_price": "#ShortTP1#",
    "tp2_price": "#ShortTP2#",
    "tp3_price": "#ShortTPFULL#",
    "tp1_pos_pct": "#TakeAmount1#",
    "tp2_pos_pct": "#TakeAmount2#",
    "tp3_pos_pct": "100",
    "sl_price": "#LongSL#"
}
```
<br >
--- [https://YOUR_BOT_NAME.herokuapp.com/commas] <br >
<br >
--- 3commas Start Bot Deal
```
{
	"key": "12345",
	"exchange": "3commas"
	"order_mode": "Bot",
	"bot_id": "#bot_id#", 
	"deal_action": "Open"	
}
```
