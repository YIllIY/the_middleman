import json
from flask import Flask, render_template, request, jsonify
from pybit.usdt_perpetual import HTTP, WebSocket
from time import sleep
from three_commas import api
import os

app = Flask(__name__)

# load config.json
with open('config.json') as config_file:
    config = json.load(config_file)

###############################################################################
#
#             This Section is for Exchange Validation
#
###############################################################################

@app.route('/')
def index():
    return {'message': 'Server is running!'}

@app.route('/bybit', methods=['POST'])
def bybit():
    print("Hook Received!")
    #data = request.form.to_dict()  ##This is for private testing locally
    data = json.loads(request.data)
    print(data)

    if int(data['key']) != config['KEY']:
        print("Invalid Key, Please Try Again!")
        return {
            "status": "error",
            "message": "Invalid Key, Please Try Again!"
        }
    use_bybit = False
    if 'BYBIT' in config['EXCHANGES']:
        if config['EXCHANGES']['BYBIT']['ENABLED']:
            print("Bybit is enabled!")
            use_bybit = True
            account = data['account']
            print(account)

        if config['EXCHANGES']['BYBIT'][account]['TESTNET']:
            session = HTTP(
                endpoint='https://api-testnet.bybit.com',
                api_key=config['EXCHANGES']['BYBIT'][account]['API_KEY'],
                api_secret=config['EXCHANGES']['BYBIT'][account]['API_SECRET']
            )
        else: 
            session = HTTP(
                endpoint='https://api.bybit.com',
                api_key=config['EXCHANGES']['BYBIT'][account]['API_KEY'],
                api_secret=config['EXCHANGES']['BYBIT'][account]['API_SECRET']
            ) 

    ##############################################################################
    #             Bybit ## MOVE THIS CODE TO NEW FILE
    ##############################################################################
    
    if data['exchange'] == 'BYBIT':
        if use_bybit:
            my_position = session.my_position(symbol=data['symbol'])
            order_side = my_position['result'][0]['side']
            mode_side = my_position['result'][0]['position_idx']
            current_mode = str(my_position['result'][0]['mode'])
            if 'close_position' in data and data['close_position'] == 'True':
                entry_side = order_side
            else:
                entry_side = data['entry_side'].capitalize()

            if 'exit_side' in data:
                exit_side = data['exit_side'].capitalize()
            else:
                if str(entry_side) == 'Buy':
                    exit_side = "Sell"
                elif str(entry_side) == 'Sell':
                    exit_side = "Buy"
                    
            current_size = my_position['result'][0]['size']    
            if 'close_pos_pct' in data:
                close_pos_pct = float(data['close_pos_pct'])/100
                close_qty = current_size * close_pos_pct
            else:
                close_qty = current_size

            if 'close_position' in data and data['close_position'] == 'True' and order_side != "None":
                if str(order_side) == 'Buy':
                    close_side = "Sell"
                elif str(order_side) == 'Sell':
                    close_side = "Buy"

                if(current_mode == 'MergedSingle'):
                    session.place_active_order(symbol=data['symbol'], order_type="Market", side=close_side,
                                                   qty=close_qty, time_in_force="GoodTillCancel", reduce_only=True,
                                                   close_on_trigger=True, position_idx=mode_side)
                if(current_mode == 'BothSide'):
                    session.close_position(symbol=data['symbol'])
                print("Closed Position")
                return {
                            "message": "Bybit Webhook Received!",
                            'status': "Success - Closed Position"
                        }
            else:
                if 'cancel_orders' in data:
                    session.cancel_all_active_orders(symbol=data['symbol'])
                    print("Cancelling Order")
                if 'type' in data:
                    my_wallet = session.get_wallet_balance()
                    current_price = session.latest_information_for_symbol(symbol=data['symbol'])['result'][0]['last_price']
                    my_token = [x for x in session.query_symbol()['result'] if x['name'] == data['symbol']]
                    quote_currency = my_token[0]['quote_currency']
                    wallet = my_wallet['result'][quote_currency]['available_balance']
                    min_price = my_token[0]['price_filter']['min_price']
                    print("Collected Info For Trade")
                    print("Setting Modes")  
                    print("Placing Order")
                    if 'entry_price' in data:
                        entry_price = data['entry_price']
                        if (entry_price == "#close#"):
                            price = float(current_price)
                        else:
                            if (min_price > entry_price):
                                price = float(min_price)
                            else:
                                price = float(entry_price)          
                    else:
                        price = 0
                    if 'sl_price' in data:
                        sl_price = float(data['sl_price'])  
                    else:
                        sl_price = 0

                    if 'stoploss_price' in data:       
                        stoploss_price = round(sl_price,4)
                    else:
                        stoploss_price = 0

                    print("Set Price: " + str(price))  
                    if 'time_in_force' in data:
                        entry_time_in_force = data['time_in_force']
                    else: 
                        entry_time_in_force = "GoodTillCancel"

                    if 'leverage' in data: 
                        print (my_token)
                        max_leverage = my_token[0]['leverage_filter']['max_leverage']  
                        requested_leverage = float(data['leverage'])
                        if data['leverage'] == 'Max':
                            set_leverage = max_leverage
                        elif(requested_leverage > max_leverage):
                            set_leverage = max_leverage
                        else:
                            set_leverage = requested_leverage
                    else:
                        set_leverage = 1
                    
                    current_leverage = my_position['result'][0]['leverage']
                    if(current_leverage != set_leverage):
                        session.set_leverage(symbol=data['symbol'], buy_leverage=set_leverage, sell_leverage=set_leverage)
                        print("Leverage Set to: " + str(set_leverage))
                    if 'take_profit_percent' in data:     
                        take_profit_percent = float(data['take_profit_percent'])/100
                    if 'stop_loss_percent' in data:
                        stop_loss_percent = float(data['stop_loss_percent'])/100
                    risk_pct = float(data['risk_pct'])/100

                    entry_size = round(risk_pct * wallet * set_leverage / price,3)
                    
########## Generic Entries ##########
                    if data['order_mode'] == 'Test':
                        return ("Mode Not Ready Yet")
                        print("Entry Price: " + str(price))

                    if data['order_mode'] == 'Both':
                        if entry_side == 'Buy':
                            take_profit_price = round(float(current_price) + (float(current_price) * take_profit_percent), 2)
                            stop_loss_price = round(float(current_price) - (float(current_price) * stop_loss_percent), 2)

                        elif entry_side == 'Sell':
                            take_profit_price = round(float(current_price) - (float(current_price) * take_profit_percent), 2)
                            stop_loss_price = round(float(current_price) + (float(current_price) * stop_loss_percent), 2)

                        session.place_active_order(symbol=data['symbol'], order_type=data['type'], side=entry_side,
                                                   qty=entry_size, time_in_force=entry_time_in_force, post_only=True, reduce_only=False,
                                                   close_on_trigger=False, price=price, take_profit=take_profit_price, stop_loss=stop_loss_price)
                        
                        print("Entry Price: " + str(price))
                        print("Take Profit Price: " + str(take_profit_price))
                        print("Stop Loss Price: " + str(stop_loss_price))
                        return {
                            "message": "Bybit Webhook Received!",
                        }

                    elif data['order_mode'] == 'Profit':
                        if entry_side == 'Buy':
                            take_profit_price = round(float(current_price) + (float(current_price) * take_profit_percent), 2)
                        elif entry_side == 'Sell':
                            take_profit_price = round(float(current_price) - (float(current_price) * take_profit_percent), 2)

                        session.place_active_order(symbol=data['symbol'], order_type=data['type'], side=entry_side,
                                                   qty=entry_size, time_in_force=entry_time_in_force, post_only=True, reduce_only=False,
                                                   close_on_trigger=False, price=price, take_profit=take_profit_price)
                        
                        print("Entry Price: " + str(price))
                        print("Take Profit Price: " + str(take_profit_price))
                        return {
                            "message": "Bybit Webhook Received!",
                        }

                    elif data['order_mode'] == 'Stop':
                        if entry_side == 'Buy':
                            stop_loss_price = round(float(current_price) - (float(current_price) * stop_loss_percent), 2)
                        elif entry_side == 'Sell':
                            stop_loss_price = round(float(current_price) + (float(current_price) * stop_loss_percent), 2)

                        session.place_active_order(symbol=data['symbol'], order_type=data['type'], side=entry_side,
                                                   qty=entry_size, time_in_force=entry_time_in_force, post_only=True, reduce_only=False,
                                                   close_on_trigger=False, price=price, stop_loss=stop_loss_price)
                        print("Entry Price: " + str(price))
                        print("Stop Loss Price: " + str(stop_loss_price))
                        return {
                            "message": "Bybit Webhook Received!",
                        }  

                    

########## Davidd ##########
                    elif data['order_mode'] == 'Davidd':
                        tp1_pos_pct = data['tp1_pos_pct']
                        tp2_pos_pct = data['tp2_pos_pct']
                        tp3_pos_pct = data['tp3_pos_pct']
                        print("Entry Size: " + str(entry_size))

                        if tp1_pos_pct != "#TakeAmount1#":
                            tp1_pos_pct = float(tp1_pos_pct)/100
                            tp1_price = float(data['tp1_price'])
                            if tp1_pos_pct == 1:
                                tp1_size = round(entry_size, 3)
                                print("Tp 100%: " + str(entry_size))
                            elif tp1_pos_pct > 0:
                                tp1_size = round(tp1_pos_pct * entry_size,3)
                                print("1Tp Size: " + str(tp1_pos_pct) + " x " + str(entry_size)  + "= " + str(tp1_size))
                        else:
                            tp1_size = 0
                            print("No Tp Set") 
                            
                        if tp2_pos_pct != "#TakeAmount2#":
                            if(tp1_size < entry_size):
                                tp2_pos_pct = float(tp2_pos_pct)/100    
                                tp2_price = float(data['tp2_price'])
                                if (tp2_pos_pct == 1) or (tp1_pos_pct + tp2_pos_pct == 1):
                                    tp2_size = round(entry_size,3)
                                    print("2Tp 100%: " + str(entry_size) + "- " + str(tp1_size))
                                elif tp2_pos_pct > 0:
                                    tp2_size = round(tp2_pos_pct * entry_size,3)
                                    print("2Tp Size: " + str(tp2_pos_pct) + " x " + str(entry_size) + " = " + str(tp2_size))
                        else:
                            tp2_size = 0
                            print("No Tp2 Set") 

                        if tp3_pos_pct != "#TakeAmountFULL#":
                            if(tp1_size + tp2_size < entry_size):
                                tp3_pos_pct = float(tp3_pos_pct)/100    
                                tp3_price = float(data['tp3_price'])
                                if (tp3_pos_pct == 1) or (tp1_pos_pct + tp2_pos_pct + tp3_pos_pct == 1):
                                    tp3_size = round(entry_size,3)
                                    print("3Tp 100%: " + str(entry_size) + " - " + str(tp1_size) + " - " + str(tp2_size) + " = " + str(tp3_size))
                                elif tp3_pos_pct > 0:
                                    tp3_size = round(tp3_pos_pct * entry_size,3)
                                    print("3Tp Size: " + str(tp3_pos_pct) + " x " + str(entry_size) + " = " + str(tp3_size))
                        else:
                            tp3_size = 0
                            print("No 3Tp Set") 

                        current_margin = my_position['result'][0]['is_isolated']
                        print("Is Isolated: " + str(current_margin))
                        if(str(current_margin) != "True"):
                            session.cross_isolated_margin_switch(symbol=data['symbol'],is_isolated=True, buy_leverage=set_leverage, sell_leverage=set_leverage)
                        
                        if(current_mode != 'MergedSingle'):
                            session.position_mode_switch(symbol=data['symbol'],mode="MergedSingle")
                        
                        current_tp_sl_mode = str(my_position['result'][0]['tp_sl_mode'])
                        if(current_tp_sl_mode != 'Full'):
                            session.full_partial_position_tp_sl_switch(symbol=data['symbol'],tp_sl_mode="Full")
                        print("Correct Modes Set:" + str(current_mode) + " / " +str(current_tp_sl_mode))

                        if entry_side == 'Buy':
                            entry_idx = 0
                        elif entry_side == 'Sell':
                            entry_idx = 0
                        if exit_side == 'Buy':
                            exit_idx = 0
                        elif exit_side == 'Sell':
                            exit_idx = 0

                        session.place_active_order(symbol=data['symbol'], order_type=data['type'], side=entry_side,
                                                   qty=entry_size, time_in_force=entry_time_in_force, post_only=True, reduce_only=False,
                                                   close_on_trigger=False, price=price, stop_loss=stoploss_price, position_idx=entry_idx)
                        print("Davidd Entry: " + str(price))
                        if data['type'] == 'Limit':
                            sleep(5)
                        else: 
                            sleep(2)

                        if (float(tp1_size) > 0):
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side=exit_side,
                                                   qty=tp1_size, time_in_force="GoodTillCancel", post_only=True, reduce_only=True,
                                                   close_on_trigger=False, price=tp1_price, position_idx=exit_idx)
                            sleep(0.5)
                            print("Davidd 1Tp Placed: " + str(tp1_price))
                        
                        if (float(tp2_size) > 0):
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side=exit_side,
                                                   qty=tp2_size, time_in_force="GoodTillCancel", post_only=True, reduce_only=True,
                                                   close_on_trigger=False, price=tp2_price, position_idx=exit_idx)
                            sleep(2)
                            print("Davidd 2Tp Placed: " + str(tp2_price))
                        
                        if (float(tp3_size) > 0):
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side=exit_side,
                                                   qty=tp3_size, time_in_force="GoodTillCancel", post_only=True, reduce_only=True,
                                                   close_on_trigger=False, price=tp3_price, position_idx=exit_idx)
                            sleep(3)
                            print("Davidd 3Tp Placed: " + str(tp3_price))
                        

                        print("Stop Loss Price: " + str(stoploss_price))
                        return {
                            "message": "Bybit Webhook Received!",
                            "status": "Success - Davvid.tech Order Processed"
                        }  

########## Lambo ##########

                    elif data['order_mode'] == 'Lambo':
                        tp1_pos_pct = data['tp1_pos_pct']
                        tp2_pos_pct = data['tp2_pos_pct']
                        tp3_pos_pct = data['tp3_pos_pct']
                        tp4_pos_pct = data['tp4_pos_pct']
                        print("Entry Size: " + str(entry_size))

                        if tp1_pos_pct != "#tp1_pos_pct#":
                            tp1_pos_pct = float(tp1_pos_pct)/100
                            tp1_price = float(data['tp1_price'])
                            if tp1_pos_pct == 1:
                                tp1_size = round(entry_size, 3)
                                print("Tp 100%: " + str(entry_size))
                            elif tp1_pos_pct > 0:
                                tp1_size = round(tp1_pos_pct * entry_size,3)
                                print("1Tp Size: " + str(tp1_pos_pct) + " x " + str(entry_size)  + " = " + str(tp1_size))
                        else:
                            tp1_size = 0
                            print("No Tp Set") 

                        if tp2_pos_pct != "#tp2_pos_pct#":
                            if(tp1_size < entry_size):
                                tp2_pos_pct = float(tp2_pos_pct)/100    
                                tp2_price = float(data['tp2_price'])
                                if (tp2_pos_pct == 1) or (tp1_pos_pct + tp2_pos_pct == 1):
                                    tp2_size = round(entry_size,3)
                                    print("2Tp 100%: " + str(entry_size) + " - " + str(tp1_size))
                                elif tp2_pos_pct > 0:
                                    tp2_size = round(tp2_pos_pct * entry_size,3)
                                    print("2Tp Size: " + str(tp2_pos_pct) + " x " + str(entry_size) + " = " + str(tp2_size))
                                else:
                                    tp2_size = 0
                                    print("No Tp2 Set") 
                        else:
                            tp2_size = 0         
                            print("No Tp 2 not enough for order")

                        if tp3_pos_pct != "#tp3_pos_pct#":
                            if(tp1_size + tp2_size < entry_size):
                                tp3_pos_pct = float(tp3_pos_pct)/100    
                                tp3_price = float(data['tp3_price'])
                                if (tp3_pos_pct == 1) or (tp1_pos_pct + tp2_pos_pct + tp3_pos_pct == 1):
                                    tp3_size = round(entry_size,3)
                                    print("3Tp 100%: " + str(entry_size) + " - " + str(tp1_size) + " - " + str(tp2_size) + " = " + str(tp3_size))
                                elif tp3_pos_pct > 0:
                                    tp3_size = round(tp3_pos_pct * entry_size,3)
                                    print("3Tp Size: " + str(tp3_pos_pct) + " x " + str(entry_size) + " = " + str(tp3_size))
                                else:
                                    tp3_size = 0
                                    print("No 3Tp Set") 
                        else:
                            tp3_size = 0
                            print("No Tp3 not enough for order")

                        if tp4_pos_pct != "#tp4_pos_pct#":
                            if(tp1_size + tp2_size + tp3_size < entry_size):
                                tp4_pos_pct = float(tp4_pos_pct)/100
                                tp4_price = float(data['tp4_price'])
                                if (tp4_pos_pct == 1) or (tp1_pos_pct + tp2_pos_pct + tp3_pos_pct + tp4_pos_pct == 1):
                                    tp4_size = round(entry_size,3)
                                    print("4Tp 100%: " + str(entry_size))
                                elif tp4_pos_pct >= 0:
                                    tp4_size = round(entry_size,3)
                                    print("4Tp Size: " + str(entry_size))    
                                else:    
                                    tp4_size = 0
                                    print("No TP 4")
                        else:
                            tp4_size = 0
                            print("No Tp4 not enough for order")

                        current_margin = my_position['result'][0]['is_isolated']
                        print("Is Isolated: " + str(current_margin))
                        if(str(current_margin) != "True"):
                            session.cross_isolated_margin_switch(symbol=data['symbol'],is_isolated=True, buy_leverage=set_leverage, sell_leverage=set_leverage)
                        
                        if(current_mode != 'MergedSingle'):
                            session.position_mode_switch(symbol=data['symbol'],mode="MergedSingle")
                        
                        current_tp_sl_mode = str(my_position['result'][0]['tp_sl_mode'])
                        if(current_tp_sl_mode != 'Full'):
                            session.full_partial_position_tp_sl_switch(symbol=data['symbol'],tp_sl_mode="Full")
                        print("Correct Modes Set:" + str(current_mode) + " / " +str(current_tp_sl_mode))

                        if entry_side == 'Buy':
                            entry_idx = 0
                        elif entry_side == 'Sell':
                            entry_idx = 0
                        if exit_side == 'Buy':
                            exit_idx = 0
                        elif exit_side == 'Sell':
                            exit_idx = 0

                        session.place_active_order(symbol=data['symbol'], order_type=data['type'], side=entry_side,
                                                   qty=entry_size, time_in_force=entry_time_in_force, post_only=True, reduce_only=False,
                                                   close_on_trigger=False, price=price, stop_loss=stoploss_price, position_idx=entry_idx)
                        print("Lambo Entry: " + str(price))
                        if data['type'] == 'Limit':
                            sleep(5)
                        else: 
                            sleep(2)

                        if (float(tp1_size) > 0):
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side=exit_side,
                                                   qty=tp1_size, time_in_force="GoodTillCancel", post_only=True, reduce_only=True,
                                                   close_on_trigger=False, price=tp1_price, position_idx=exit_idx)
                            sleep(0.5)
                            print("Lambo 1Tp Placed: " + str(tp1_price))
                        
                        if (float(tp2_size) > 0):
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side=exit_side,
                                                   qty=tp2_size, time_in_force="GoodTillCancel", post_only=True, reduce_only=True,
                                                   close_on_trigger=False, price=tp2_price, position_idx=exit_idx)
                            sleep(2)
                            print("Lambo 2Tp Placed: " + str(tp2_price))
                        
                        if (float(tp3_size) > 0):
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side=exit_side,
                                                   qty=tp3_size, time_in_force="GoodTillCancel", post_only=True, reduce_only=True,
                                                   close_on_trigger=False, price=tp3_price, position_idx=exit_idx)
                            sleep(3)
                            print("Lambo 3Tp Placed: " + str(tp3_price))
                        
                        if (float(tp4_size) > 0):
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side=exit_side,
                                                   qty=tp4_size, time_in_force="GoodTillCancel", post_only=True, reduce_only=True,
                                                   close_on_trigger=False, price=tp4_price, position_idx=exit_idx)
                            print("Lambo 4Tp Placed: " + str(tp4_price))

                        print("Stop Loss Price: " + str(stoploss_price))
                        return {
                            "message": "Bybit Webhook Received!",
                            "status": "Success - Lambo Order Processed"
                        }  

########## Acrypto ##########

                    elif data['order_mode'] == 'Acrypto':
                        tp1_pos_pct = data['tp1_pos_pct']
                        tp2_pos_pct = data['tp2_pos_pct']
                        tp3_pos_pct = data['tp3_pos_pct']
                        tp4_pos_pct = data['tp4_pos_pct']
                        tp5_pos_pct = data['tp5_pos_pct']
                        tp6_pos_pct = data['tp6_pos_pct']
                        print("Entry Size: " + str(entry_size))

                        if tp1_pos_pct != "#tp1_pos_pct#":
                            tp1_pos_pct = float(tp1_pos_pct)/100
                            tp1_price = float(data['tp1_price'])
                            if tp1_pos_pct == 1:
                                tp1_size = round(entry_size, 3)
                                print("Tp 100%: " + str(entry_size))
                            elif tp1_pos_pct > 0:
                                tp1_size = round(tp1_pos_pct * entry_size,3)
                                print("1Tp Size: " + str(tp1_pos_pct) + " x " + str(entry_size)  + " = " + str(tp1_size))
                        else:
                            tp1_size = 0
                            print("No Tp Set") 

                        if tp2_pos_pct != "#tp2_pos_pct#":
                            if(tp1_size < entry_size):
                                tp2_pos_pct = float(tp2_pos_pct)/100    
                                tp2_price = float(data['tp2_price'])
                                if (tp2_pos_pct == 1) or (tp1_pos_pct + tp2_pos_pct == 1):
                                    tp2_size = round(entry_size,3)
                                    print("2Tp 100%: " + str(entry_size) + " - " + str(tp1_size))
                                elif tp2_pos_pct > 0:
                                    tp2_size = round(tp2_pos_pct * entry_size,3)
                                    print("2Tp Size: " + str(tp2_pos_pct) + " x " + str(entry_size) + " = " + str(tp2_size))
                                else:
                                    tp2_size = 0
                                    print("No Tp2 Set") 
                        else:
                            tp2_size = 0         
                            print("No Tp 2 not not enough for order")

                        if tp3_pos_pct != "#tp3_pos_pct#":
                            if(tp1_size + tp2_size < entry_size):
                                tp3_pos_pct = float(tp3_pos_pct)/100    
                                tp3_price = float(data['tp3_price'])
                                if (tp3_pos_pct == 1) or (tp1_pos_pct + tp2_pos_pct + tp3_pos_pct == 1):
                                    tp3_size = round(entry_size,3)
                                    print("3Tp 100%: " + str(entry_size) + " - " + str(tp1_size) + " - " + str(tp2_size) + " = " + str(tp3_size))
                                elif tp3_pos_pct > 0:
                                    tp3_size = round(tp3_pos_pct * entry_size,3)
                                    print("3Tp Size: " + str(tp3_pos_pct) + " x " + str(entry_size) + " = " + str(tp3_size))
                                else:
                                    tp3_size = 0
                                    print("No 3Tp Set") 
                        else:
                            tp3_size = 0
                            print("No Tp3 not not enough for order")

                        if tp4_pos_pct != "#tp4_pos_pct#":
                            if(tp1_size + tp2_size + tp3_size < entry_size):
                                tp4_pos_pct = float(tp4_pos_pct)/100
                                tp4_price = float(data['tp4_price'])
                                if (tp4_pos_pct == 1) or (tp1_pos_pct + tp2_pos_pct + tp3_pos_pct + tp4_pos_pct == 1):
                                    tp4_size = round(entry_size,3)
                                    print("4Tp 100%: " + str(entry_size))
                                elif tp4_pos_pct >= 0:
                                    tp4_size = round(entry_size,3)
                                    print("4Tp Size: " + str(entry_size))    
                                else:    
                                    tp4_size = 0
                                    print("No TP 4")
                        else:
                            tp4_size = 0
                            print("No Tp4 not not enough for order")
                        
                        if tp5_pos_pct != "#tp5_pos_pct#":
                            if(tp1_size + tp2_size + tp3_size + tp4_size < entry_size):
                                tp5_pos_pct = float(tp5_pos_pct)/100
                                tp5_price = float(data['tp5_price'])
                                if (tp5_pos_pct == 1) or (tp1_pos_pct + tp2_pos_pct + tp3_pos_pct + tp4_pos_pct + tp5_pos_pct == 1):
                                    tp5_size = round(entry_size,3)
                                    print("4Tp 100%: " + str(entry_size))
                                elif tp5_pos_pct >= 0:
                                    tp5_size = round(entry_size,3)
                                    print("5Tp Size: " + str(entry_size))    
                                else:    
                                    tp4_size = 0
                                    print("No TP 5")
                        else:
                            tp5_size = 0
                            print("No Tp5 not not enough for order")

                        if tp6_pos_pct != "#tp6_pos_pct#":
                            if(tp1_size + tp2_size + tp3_size + tp4_size + tp5_size < entry_size):
                                tp6_pos_pct = float(tp6_pos_pct)/100
                                tp6_price = float(data['tp6_price'])
                                if (tp6_pos_pct == 1) or (tp1_pos_pct + tp2_pos_pct + tp3_pos_pct + tp4_pos_pct + tp5_size + tp6_size == 1):
                                    tp6_size = round(entry_size,3)
                                    print("6Tp 100%: " + str(entry_size))
                                elif tp6_pos_pct >= 0:
                                    tp6_size = round(entry_size,3)
                                    print("6Tp Size: " + str(entry_size))    
                                else:    
                                    tp6_size = 0
                                    print("No TP 6")
                        else:
                            tp6_size = 0
                            print("No Tp6 not not enough for order")    

                        current_margin = my_position['result'][0]['is_isolated']
                        print("Is Isolated: " + str(current_margin))
                        if(str(current_margin) != "True"):
                            session.cross_isolated_margin_switch(symbol=data['symbol'],is_isolated=True, buy_leverage=set_leverage, sell_leverage=set_leverage)
                        
                        if(current_mode != 'MergedSingle'):
                            session.position_mode_switch(symbol=data['symbol'],mode="MergedSingle")
                        
                        current_tp_sl_mode = str(my_position['result'][0]['tp_sl_mode'])
                        if(current_tp_sl_mode != 'Full'):
                            session.full_partial_position_tp_sl_switch(symbol=data['symbol'],tp_sl_mode="Full")
                        print("Correct Modes Set:" + str(current_mode) + " / " +str(current_tp_sl_mode))

                        if entry_side == 'Buy':
                            entry_idx = 0
                        elif entry_side == 'Sell':
                            entry_idx = 0
                        if exit_side == 'Buy':
                            exit_idx = 0
                        elif exit_side == 'Sell':
                            exit_idx = 0

                        session.place_active_order(symbol=data['symbol'], order_type=data['type'], side=entry_side,
                                                   qty=entry_size, time_in_force=entry_time_in_force, post_only=True, reduce_only=False,
                                                   close_on_trigger=False, price=price, stop_loss=stoploss_price, position_idx=entry_idx)
                        print("Acryto Entry: " + str(price))
                        if data['type'] == 'Limit':
                            sleep(5)
                        else: 
                            sleep(2)

                        if (float(tp1_size) > 0):
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side=exit_side,
                                                   qty=tp1_size, time_in_force="GoodTillCancel", post_only=True, reduce_only=True,
                                                   close_on_trigger=False, price=tp1_price, position_idx=exit_idx)
                            sleep(0.5)
                            print("Acryto 1Tp Placed: " + str(tp1_price))
                        
                        if (float(tp2_size) > 0):
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side=exit_side,
                                                   qty=tp2_size, time_in_force="GoodTillCancel", post_only=True, reduce_only=True,
                                                   close_on_trigger=False, price=tp2_price, position_idx=exit_idx)
                            sleep(2)
                            print("Acryto 2Tp Placed: " + str(tp2_price))
                        
                        if (float(tp3_size) > 0):
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side=exit_side,
                                                   qty=tp3_size, time_in_force="GoodTillCancel", post_only=True, reduce_only=True,
                                                   close_on_trigger=False, price=tp3_price, position_idx=exit_idx)
                            sleep(3)
                            print("Acryto 3Tp Placed: " + str(tp3_price))
                        
                        if (float(tp4_size) > 0):
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side=exit_side,
                                                   qty=tp4_size, time_in_force="GoodTillCancel", post_only=True, reduce_only=True,
                                                   close_on_trigger=False, price=tp4_price, position_idx=exit_idx)
                            print("Acryto 4Tp Placed: " + str(tp4_price))
                        
                        if (float(tp5_size) > 0):
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side=exit_side,
                                                   qty=tp5_size, time_in_force="GoodTillCancel", post_only=True, reduce_only=True,
                                                   close_on_trigger=False, price=tp5_price, position_idx=exit_idx)
                            print("Acryto 5Tp Placed: " + str(tp5_price))
                        
                        if (float(tp6_size) > 0):
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side=exit_side,
                                                   qty=tp6_size, time_in_force="GoodTillCancel", post_only=True, reduce_only=True,
                                                   close_on_trigger=False, price=tp6_price, position_idx=exit_idx)
                            print("Acryto 6Tp Placed: " + str(tp6_price))

                        print("Stop Loss Price: " + str(stoploss_price))
                        return {
                            "message": "Bybit Webhook Received!",
                            "status": "Success - Acrypto Order Processed"     
                        }  


########## Genie ##########

                    elif data['order_mode'] == 'Genie':
                        if(current_mode != 'BothSide'):
                            session.position_mode_switch(symbol=data['symbol'],mode="BothSide")
                        
                        current_tp_sl_mode = str(my_position['result'][0]['tp_sl_mode'])
                        if(current_tp_sl_mode != 'Partial'):
                            session.full_partial_position_tp_sl_switch(symbol=data['symbol'],tp_sl_mode="Partial")
                        print("Correct Modes Set " + str(current_mode) + " " +str(current_tp_sl_mode))

                        current_margin = my_position['result'][0]['is_isolated']
                        print("Is Isolated: " + str(current_margin))
                        if(str(current_margin) == "True"):
                            session.cross_isolated_margin_switch(symbol=data['symbol'],is_isolated=False, buy_leverage=set_leverage, sell_leverage=set_leverage)

                        if entry_side == 'Buy':
                            entry_idx = 1
                        elif entry_side == 'Sell':
                            entry_idx = 2
                        if float(data['long_price1']) > 0:
                            long_size1 = round(float(data['long_pct1'])/100 * wallet * set_leverage / float(data['long_price1']),3)
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side="Buy",
                                                    qty=long_size1, time_in_force="GoodTillCancel", post_only=True, reduce_only=False,
                                                    close_on_trigger=False, price=data['long_price1'], position_idx="1")
                        if float(data['short_price1']) > 0:
                            short_size1 = round(float(data['short_pct1'])/100 * wallet * set_leverage / float(data['short_price1']),3)
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side="Sell",
                                                    qty=short_size1, time_in_force="GoodTillCancel", post_only=True, reduce_only=False,
                                                    close_on_trigger=False, price=data['short_price1'], position_idx="2") 
                        print("Orders 1 Placed")
                        sleep(0.5)                                                                            
                        if float(data['long_price2']) > 0:
                            long_size2 = round(float(data['long_pct2'])/100 * wallet * set_leverage / float(data['long_price2']),3)
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side="Buy",
                                                    qty=long_size2, time_in_force="GoodTillCancel", post_only=True, reduce_only=False,
                                                    close_on_trigger=False, price=data['long_price2'], position_idx="1")
                        if float(data['short_price2']) > 0:
                            short_size2 = round(float(data['short_pct2'])/100 * wallet * set_leverage / float(data['short_price2']),3)
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side="Sell",
                                                    qty=short_size2, time_in_force="GoodTillCancel", post_only=True, reduce_only=False,
                                                    close_on_trigger=False, price=data['short_price2'], position_idx="2") 
                        print("Orders 2 Placed")
                        sleep(0.5)    
                        if float(data['long_price3']) > 0:
                            long_size3 = round(float(data['long_pct3'])/100 * wallet * set_leverage / float(data['long_price3']),3)
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side="Buy",
                                                    qty=long_size3, time_in_force="GoodTillCancel", post_only=True, reduce_only=False,
                                                    close_on_trigger=False, price=data['long_price3'], position_idx="1")
                        if float(data['short_price3']) > 0:
                            short_size3 = round(float(data['short_pct3'])/100 * wallet * set_leverage / float(data['short_price3']),3)
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side="Sell",
                                                    qty=short_size3, time_in_force="GoodTillCancel", post_only=True, reduce_only=False,
                                                    close_on_trigger=False, price=data['short_price3'], position_idx="2") 
                        print("Orders 3 Placed")
                        sleep(1)    
                        if float(data['long_price4']) > 0:
                            long_size4 = round(float(data['long_pct4'])/100 * wallet * set_leverage / float(data['long_price4']),3)
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side="Buy",
                                                    qty=long_size4, time_in_force="GoodTillCancel", post_only=True, reduce_only=False,
                                                    close_on_trigger=False, price=data['long_price4'], position_idx="1")
                        if float(data['short_price4']) > 0:
                            short_size4 = round(float(data['short_pct4'])/100 * wallet * set_leverage / float(data['short_price4']),3)
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side="Sell",
                                                    qty=short_size4, time_in_force="GoodTillCancel", post_only=True, reduce_only=False,
                                                    close_on_trigger=False, price=data['short_price4'], position_idx="2") 
                        print("Orders 4 Placed")
                        sleep(1)    
                        if float(data['long_price5']) > 0:
                            long_size5 = round(float(data['long_pct5'])/100 * wallet * set_leverage / float(data['long_price5']),3)
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side="Buy",
                                                    qty=long_size5, time_in_force="GoodTillCancel", post_only=True, reduce_only=False,
                                                    close_on_trigger=False, price=data['long_price5'], position_idx="1")
                        if float(data['short_price5']) > 0:
                            short_size5 = round(float(data['short_pct5'])/100 * wallet * set_leverage / float(data['short_price5']),3)
                            session.place_active_order(symbol=data['symbol'], order_type="Limit", side="Sell",
                                                    qty=short_size5, time_in_force="GoodTillCancel", post_only=True, reduce_only=False,
                                                    close_on_trigger=False, price=data['short_price5'], position_idx="2")  
                        print("Orders 5 Placed")
                        return {
                            "message": "Bybit Webhook Received!",
                            "status": "Success - Genie Order Processed"           
                        }  

                    else:
                        return ("Error - Check Your Mode")

        return {
            "status": "Success",
            "message": "Bybit Webhook Received! - But Order Did not Fire Check your Json"
        }

    else:
        print("Invalid Exchange, Please Try Again!")
        return {
            "status": "error",
            "message": "Invalid Exchange, Please Try Again!"
        }


@app.route('/commas', methods=['POST'])
def commas():
    print("Hook Received!")
    #data = request.form.to_dict()  ##This is for private testing locally
    data = json.loads(request.data)
    print(data)
    if int(data['key']) != config['KEY']:
        print("Invalid Key, Please Try Again!")
        return {
            "status": "error",
            "message": "Invalid Key, Please Try Again!"
        }
    use_3commas = False
    if '3COMMAS' in config['EXCHANGES']:
        if config['EXCHANGES']['3COMMAS']['ENABLED']:
            os.environ["THREE_COMMAS_API_KEY"] = config['EXCHANGES']['3COMMAS']['API_KEY']
            os.environ["THREE_COMMAS_API_SECRET"] = config['EXCHANGES']['3COMMAS']['API_SECRET']
            if 'account' in data:
                account_import = data['account'].upper()
                account = config['EXCHANGES']['3COMMAS'][account_import]
            else:
                account = 0
            print("3commas is enabled!")
            use_3commas = True
        if data['order_mode'] == 'Account':
            account_data = api.ver1.accounts.get()
            print(account_data)  
            return{ 
                'message': '3commas Webhook Recieved',
                'status': 'Account Info Test'
                }
        if data['order_mode'] == 'Bot': ## Create Bot - Coming Soon
            if data['deal_action'] == 'Create':
                create_bot = {
                    "account_id": account,
                    "name": data['name'],
                    "pairs": data['pairs'],
                    "base_order_volume": data['base_order_volume'],
                    "safety_order_volume": data['safety_order_volume'],
                    "take_profit":data['take_profit'],
                    "take_profit_type": data['take_profit_type'],
                    "strategy": data['strategy'],
                    "start_order_type": data['start_order_type'],
                    "strategy_list": [{"strategy":"manual"}],
                    "max_safety_orders": data['max_safety_orders'],
                    "active_safety_orders_count": data['active_safety_orders_count'],
                    "safety_order_step_percentage": data['safety_order_step_percentage'],
                    "martingale_volume_coefficient":data['martingale_volume_coefficient'],
                    "martingale_step_coefficient": data['martingale_step_coefficient'],
                    "profit_currency":data['profit_currency'],
                }
                error, create_bot_response = api.ver1.bots.post_create_bot(create_bot)
                if not error:
                    print(create_bot_response)
                    return {
                    'message': '3commas Webhook Recieved',
                    'status': 'Bot Created'
                    }
                else:
                    print(error)
                    return{ 
                        'message': '3commas Webhook Recieved',
                        'status': 'ERROR: Bot NOT Created'
                    }
            if data['deal_action'] == 'Update':
                bot_id = data['bot_id']
                update_bot = {
                    "name": data['name'],
                    "pairs": data['pairs'],
                    "base_order_volume": data['base_order_volume'],
                    "safety_order_volume": data['safety_order_volume'],
                    "take_profit":data['take_profit'],
                    "take_profit_type": data['take_profit_type'],
                    "strategy": data['strategy'],
                    "start_order_type": data['start_order_type'],
                    "strategy_list": [{"strategy":"manual"}],
                    "max_safety_orders": data['max_safety_orders'],
                    "active_safety_orders_count": data['active_safety_orders_count'],
                    "safety_order_step_percentage": data['safety_order_step_percentage'],
                    "martingale_volume_coefficient":data['martingale_volume_coefficient'],
                    "martingale_step_coefficient": data['martingale_step_coefficient'],
                    "profit_currency":data['profit_currency'],
                }
                error, create_bot_response = api.ver1.bots.patch_update_by_id(bot_id,update_bot)
                if not error:
                    print(create_bot_response)
                    return {
                    'message': '3commas Webhook Recieved',
                    'status': 'Bot Created'
                    }
                else:
                    print(error)
                    return{ 
                        'message': '3commas Webhook Recieved',
                        'status': 'ERROR: Bot NOT Created'
                    }        
            if data['deal_action'] == 'Close':
                get_deals = {
                    "bot_id": data['bot_id'],
                    "Finished?": False
                }
                error, get_deals_response = api.ver1.deals.get(get_deals)
                close_bot_id = get_deals_response[0]['id']
                error, panic_sell_response = api.ver1.deals.post_panic_sell_by_id(close_bot_id)
                print(panic_sell_response)
                return {
                    'message': '3commas Webhook Recieved',
                    'status': 'Deal Closed'
                }
            if data['deal_action'] == 'Open':
                error, start_deal_response = api.ver1.bots.post_start_new_deal_by_id(data['bot_id'])
                print(start_deal_response)
                return {
                    'message': '3commas Webhook Recieved',
                    'status': 'Deal Opened'
                }
            if data['deal_action'] == 'Convert':
                get_deals = {
                    "bot_id": data['bot_id'],
                    "Finished?": False
                }
                error, get_deals_response = api.ver1.deals.get(get_deals)
                convert_bot_id = get_deals_response[0]['id']
                error, convert_response = api.ver1.deals.post_convert_to_smart_trade_by_id(convert_bot_id)
                print(convert_response)
                return {
                    'message': '3commas Webhook Recieved',
                    'status': 'Deal Converted to SmartTrade'
                }
            if data['deal_action'] == 'SafetyOrder':
                get_deal = {
                    "bot_id": data['bot_id'],
                    "Finished?": False
                } 
                error, get_deal_response = api.ver1.deals.get(get_deal)
                so_deal_id = get_deal_response[0]['id']
                safety_order_id = {
                    "deal_id": so_deal_id,
                    "is_market": True,
                    "rate": "1.00", #used for limit order / is_market: false
                    "quantity": data['volume']
                }
                error, so_response = api.ver1.deals.post_add_funds_by_id(safety_order_id)
                print(so_response)
                return {
                    'message': '3commas Webhook Recieved',
                    'status': 'Funds Added to Deal'
                }
            if data['deal_action'] == 'Test':
                get_deals = {
                    "bot_id": data['bot_id'],
                    "Finished?": False
                }
                error, get_deals_response = api.ver1.deals.get(get_deals)
                convert_bot_id = get_deals_response[0]['id']
                print(convert_bot_id)
                update_deal = {
                    "stop_loss_percentage": data['stop_loss'],
                    "take_profit": data['take_profit'],
                }
                # update_bot = {"tsl_enabled": True}
                update_response = api.ver1.deals.patch_update_deal_by_id(convert_bot_id, update_deal)
                # update_bot = api.ver1.bots.patch_update_by_id(data['bot_id'])
                print(update_response)
                # print(update_bot)
                return {
                    'message': '3commas Webhook Recieved',
                    'status': 'Deal Updated'
                }
        if data['order_mode'] == 'SmartTrade': # Smart Trade - Coming Soon
            if data['deal_action'] == 'Create':
                entry_price = float(data['entry_price'])
                if float(data['take_profit']) == 0:
                    take_profit = "false"
                else:
                    take_profit = "true"
                    tp1_price = "1.00"
                if float(data['stop_loss']) == 0:
                    stop_loss = "false"

                smart_trade = {
                    "account_id": account,
                    "pair": data['pair'],
                    "position": {
                        "type": data['position'],
                        "order_type": data['order_type'],
                        "units": {
                            "value": data['totat_qty']
                        },
                        "total": {
                            "value": entry_price
                        }
                    },
                    "take_profit": {
                        "enabled": take_profit,
                        # "steps": [
                        #    {
                        #    "order_type": "limit",
                        #    "price": {
                        #        "value": tp1_price,
                        #        "type": "bid"
                        #    },
                        #    "volume": "100"
                        #    }
                        #]      
                    },
                    "stop_loss": {
                        "enabled": stop_loss,
                        # "order_type": data['stop_loss']['order_type'],
                        # "price": {
                        #    "value": data['stop_loss']['price']['value']
                        # },
                        # "conditional": {
                        #    "price": {
                        #        "value": data['stop_loss']['conditional']['price']['value'],
                        #        "type": data['stop_loss']['conditional']['price']['type']
                        #    }
                        # }
                    }
                }
                smart_trade_response = api.v2.smart_trades.post(smart_trade)
                print(smart_trade_response)
                return {
                    'message': '3commas Webhook Recieved',
                    'status': 'SmartTrade Open'
                }
            if data['deal_action'] == 'Update_TPSL':
                account_id = account,
                trade_id = data['trade_id']
                stop_loss = float(data['stop_loss'])/100
                take_profit = float(data['take_profit'])/100
                smart_trade_info = api.v2.smart_trades.get_by_id(trade_id)
                print(smart_trade_info)
                avg_price = float(smart_trade_info[1]['position']['price']['value']) 
                current_price = float(smart_trade_info[1]['data']['current_price']['bid'])
                profit = float(smart_trade_info[1]['profit']['percent'])
                if str(data['enable_sl']) == "true":
                    if str(data['lock_in_profit']) == "true":
                        stop_loss_value = avg_price + (avg_price * stop_loss)
                        sl_enabled = True
                    else:    
                        stop_loss_value = avg_price - (avg_price * stop_loss)
                        sl_enabled = True
                elif str(data['enable_sl']) == "false":
                    sl_enabled = False
                    stop_loss_value = "0"
                if str(data['enable_tp']) == "true":    
                    if str(data['update_tp']) == "true":
                        take_profit_value = avg_price + (avg_price * take_profit)
                        tp_enabled = True
                        steps = [
                                    {
                                        "order_type": "limit",
                                        "price": {                         
                                            "value":take_profit_value,
                                            "type":"bid",
                                        },                
                                        "volume": "100",                   
                                    },
                                ]  
                print(profit)
                smart_trade = {   
                    "position": {
                        "type": smart_trade_info[1]['position']['type'],
                        "order_type": smart_trade_info[1]['position']['order_type'],
                        "units": {
                            "value": smart_trade_info[1]['position']['units']['value']
                        },
                    },
                    "take_profit": {                               
                        "enabled": tp_enabled,                    
                        "steps": steps
                    },  
                    "stop_loss": {                                 
                        "enabled": sl_enabled,                   
                        "breakeven":"false",                  
                        "order_type": "limit",              
                        "price": {                                  
                            "value":stop_loss_value
                        },
                        "conditional": {                           
                            "price": {                             
                                "value": stop_loss_value,                  
                                "type":"bid",                                
                            },
                            "trailing": {                          
                                "enabled":False              
                            }            
                        }
                    }
                }
                smart_trade_response = api.v2.smart_trades.patch_by_id(trade_id,smart_trade)
                print(smart_trade_response)
                return {
                    'message': '3commas Webhook Recieved',
                    'status': 'SmartTrade TP / SL Updated'
                }
            if data['deal_action'] == 'Update_TP':
                account_id = account,
                trade_id = data['trade_id']
                stop_loss = float(data['stop_loss'])/100
                take_profit = float(data['take_profit'])/100
                smart_trade_info = api.v2.smart_trades.get_by_id(trade_id)
                print(smart_trade_info)
                avg_price = float(smart_trade_info[1]['position']['price']['value']) 
                current_price = float(smart_trade_info[1]['data']['current_price']['bid'])
                profit = float(smart_trade_info[1]['profit']['percent'])
                if str(data['enable_sl']) == "true":
                    if str(data['lock_in_profit']) == "true":
                        stop_loss_value = avg_price + (avg_price * stop_loss)
                        sl_enabled = True
                    else:    
                        stop_loss_value = avg_price - (avg_price * stop_loss)
                        sl_enabled = True
                elif str(data['enable_sl']) == "false":
                    sl_enabled = False
                    stop_loss_value = "0"
                if str(data['enable_tp']) == "true":    
                    if str(data['update_tp']) == "true":
                        take_profit_value = avg_price + (avg_price * take_profit)
                        tp_enabled = True
                        steps = [
                                    {
                                        "order_type": "limit",
                                        "price": {                         
                                            "value":take_profit_value,
                                            "type":"bid",
                                        },                
                                        "volume": "100",                   
                                    },
                                ]  
                print(profit)
                smart_trade = {   
                    "position": {
                        "type": smart_trade_info[1]['position']['type'],
                        "order_type": smart_trade_info[1]['position']['order_type'],
                        "units": {
                            "value": smart_trade_info[1]['position']['units']['value']
                        },
                    },
                    "take_profit": {                               
                        "enabled": tp_enabled,                    
                        "steps": steps
                    },  
                    "stop_loss": {                                 
                        "enabled": sl_enabled,                   
                        "breakeven":"false",                  
                        "order_type": "limit",              
                        "price": {                                  
                            "value":stop_loss_value
                        },
                        "conditional": {                           
                            "price": {                             
                                "value": stop_loss_value,                  
                                "type":"bid",                                
                            },
                            "trailing": {                          
                                "enabled":False              
                            }            
                        }
                    }
                }
                smart_trade_response = api.v2.smart_trades.patch_by_id(trade_id,smart_trade)
                print(smart_trade_response)
                return {
                    'message': '3commas Webhook Recieved',
                    'status': 'SmartTrade TP Updated'
                }
            if data['deal_action'] == 'Update_SL':
                account_id = account,
                trade_id = data['trade_id']
                stop_loss = float(data['stop_loss'])/100
                take_profit = float(data['take_profit'])/100
                smart_trade_info = api.v2.smart_trades.get_by_id(trade_id)
                print(smart_trade_info)
                avg_price = float(smart_trade_info[1]['position']['price']['value']) 
                current_price = float(smart_trade_info[1]['data']['current_price']['bid'])
                profit = float(smart_trade_info[1]['profit']['percent'])
                if str(data['enable_sl']) == "true":
                    if str(data['lock_in_profit']) == "true":
                        stop_loss_value = avg_price + (avg_price * stop_loss)
                        sl_enabled = True
                    else:    
                        stop_loss_value = avg_price - (avg_price * stop_loss)
                        sl_enabled = True
                elif str(data['enable_sl']) == "false":
                    sl_enabled = False
                    stop_loss_value = "0"
                if str(data['enable_tp']) == "true":    
                    if str(data['update_tp']) == "true":
                        take_profit_value = avg_price + (avg_price * take_profit)
                        tp_enabled = True
                        steps = [
                                    {
                                        "order_type": "limit",
                                        "price": {                         
                                            "value":take_profit_value,
                                            "type":"bid",
                                        },                
                                        "volume": "100",                   
                                    },
                                ]  
                print(profit)
                smart_trade = {   
                    "position": {
                        "type": smart_trade_info[1]['position']['type'],
                        "order_type": smart_trade_info[1]['position']['order_type'],
                        "units": {
                            "value": smart_trade_info[1]['position']['units']['value']
                        },
                    },
                    "take_profit": {                               
                        "enabled": tp_enabled,                    
                        "steps": steps
                    },  
                    "stop_loss": {                                 
                        "enabled": sl_enabled,                   
                        "breakeven":"false",                  
                        "order_type": "limit",              
                        "price": {                                  
                            "value":stop_loss_value
                        },
                        "conditional": {                           
                            "price": {                             
                                "value": stop_loss_value,                  
                                "type":"bid",                                
                            },
                            "trailing": {                          
                                "enabled":False              
                            }            
                        }
                    }
                }
                smart_trade_response = api.v2.smart_trades.patch_by_id(trade_id,smart_trade)
                print(smart_trade_response)
                return {
                    'message': '3commas Webhook Recieved',
                    'status': 'SmartTrade SL Updated'
                }
    return {
        'message': '3commas Webhook Recieved',
        'status': 'Error: Something Probably went Wrong'
        }

if __name__ == '__main__':
    app.run(debug=False)
