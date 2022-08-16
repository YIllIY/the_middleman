
This is a spin-off of the Crypto-Gnome Bot Modded to work for me and my Strategy on Tradingview. <br >(original bot here https://github.com/CryptoGnome/Tradingview-Webhook-Bot)

A tradingview webhook designed to be free & open source.  This bot is written using Python & Flask and is designed to run a free heroku server or Docker. 

#### Support can be requested in our Discord:

# How to Webhook Server on Heroku

1.) Fork Project to your Own Github

2.) [Create Free Heroku Account](https://www.heroku.com/)

3.) Edit config.json to add your own api keys & add a custom key to protect the server.

```You need to creat new keys on Bybit & give them the correct acess to trade and see token balance```
	
4. Create New App.

5. Connect your App to your Github

6. Deploy.

--- Other Option is use docker  -- Dont ask me to suppor though... I am new to this too ... but I managed to figure it out from Vultr... and a new docker image.
```
sudo docker build --tag insane-bot .
```
```
sudo docker run -d -p 80:5000 insane-bot
```

If needed
```
sudo docker container ls
```

```
sudo docker stop <container-name>
```
```
sudo docker container prune
```

# How to send alerts from TradingView to your new Webserver

After starting you server, you shoudl see an address that will allow you to access it like below:<br >

[https://YOUR_BOT_NAME.herokuapp.com/byit]

_Now when your alerts fire off they should go strait to your server and get proccessed on the exchange almost instantly!_

Right Now There are 2 Modes<br >
Genie - For GENIE Entries - Currently ONLY Supports 1 Entry at a time. <br >
Lambo - For LamboModd Strategy<br >
Davidd - For Davidd.tech Strategy

# TradingView Alerts Format 

-- Reduce Funds Long / Short ANY Strategy with % to leave a a little open (except 3commas)
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
-- FULL Exit Long / Short ANY Strategy (except 3commas)
```
{
	"key": "12345",
	"exchange": "#exchange#",
	"symbol": "#symbol#",
	"close_position": "True",
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
--- Acrypto Strategy w/ v2.3 LamboRambo Placeholders
```
{
    "key": "12345",
    "order_mode": "Acrypto",
    "exchange": "#exchange#",
    "symbol": "#symbol#",
    "cancel_orders": "True",
    "type": "Market",
    "time_in_force": "GoodTillCancel",
    "entry_side": "#entry_side#",
    "exit_side": "#exit_side#",
    "risk_pct": "#risk_pct#",
    "leverage": "#leverage#",
    "entry_price": "#close#", 
    "tp1_price": "#tp1_price#",
    "tp2_price": "#tp2_price#",
    "tp3_price": "#tp3_price#",
    "tp4_price": "#tp4_price#",
    "tp5_price": "#tp5_price#",
    "tp6_price": "#tp6_price#",
    "tp1_pos_pct": "#tp1_pos_pct#",
    "tp2_pos_pct": "#tp2_pos_pct#",
    "tp3_pos_pct": "#tp3_pos_pct#",
    "tp4_pos_pct": "#tp4_pos_pct#",
    "tp5_pos_pct": "#tp5_pos_pct#",
    "tp6_pos_pct": "#tp6_pos_pct#",
    "sl_price": "#sl_price#"
} 
```
--- Genie Strategy - coming soon
```
{
	"key": "12345",
	"account": "Bybit",
	"order_mode": "Genie",
	"exchange": "#exchange#",
	"symbol": "#symbol#",
	"type": "Limit",
	"entry_side": "Buy",
	"risk_pct": "0",
	"leverage": "#leverage#",
	"entry_price": "#close#",
	"long_price1": "#long_price1#",
	"long_price2": "#long_price2#",
	"long_price3": "#long_price3#",
	"long_price4": "#long_price4#",
	"long_price5": "#long_price5#",
	"short_price1": "#short_price1#",
	"short_price2": "#short_price2#",
	"short_price3": "#short_price3#",
	"short_price4": "#short_price4#",
	"short_price5": "#short_price5#",
	"long_pct1": "#long_pct1#",
	"long_pct2": "#long_pct2#",
	"long_pct3": "#long_pct3#",
	"long_pct4": "#long_pct4#",
	"long_pct5": "#long_pct5#",
	"short_pct1": "#short_pct1#",
	"short_pct2": "#short_pct2#",
	"short_pct3": "#short_pct3#",
	"short_pct4": "#short_pct4#",
	"short_pct5": "#short_pct5#"
}

```
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
--- 3commas Panic Sell Bot Deal
```
{
	"key": "12345",
	"exchange": "3commas"
	"order_mode": "Bot",
	"bot_id": "#bot_id#", 
	"deal_action": "Close"	
}
```
--- 3commas Panic Convert Bot Deal
```
{
	"key": "12345",
	"exchange": "3commas"
	"order_mode": "Bot",
	"bot_id": "#bot_id#", 
	"deal_action": "Convert"	
}
```

