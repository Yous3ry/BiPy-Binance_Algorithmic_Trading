# references
# Websocket in Binance https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md
# Binance Python API https://python-binance.readthedocs.io/en/latest/
# other Binance Websocket https://python-binance.readthedocs.io/en/latest/websockets.html
# Telegram bot # https://docs.telethon.dev/en/latest/basic/quick-start.html

# pip install websocket-client
import gc  # used to get all coin objects
import websocket  # used to send and receive live data
import json  # used to get received data
# You MUST manually run Twisted file
# pip install D:\BiPy_V1.0\Other_Files\Twisted-20.3.0-cp39-cp39-win_amd64.whl
# pip install python-binance
from binance.client import Client  # used to connect to Binance
from binance.enums import *  # used to get buy and sell signals
import pandas as pd  # used for data manipulation
import datetime as dt  # used for datetime
import requests  # used for API history loading
import math  # used for rounding
from ta import trend as ta_trend  # used to calculate the different trend indicators
from ta import momentum as ta_momentum  # used to calculate the different momentum indicators
import time  # used for delay during re-connection
# pip install telethon
from telethon import TelegramClient  # used for Telegram bot
import numpy as np  # used to transform lists
from os import path  # used to check if history files exist
import os  # used for system time sync


# Key and Secret Key from Binance
API_Key = "Enter your key here"
API_Secret = "Enter your secret key here"


# Bot Name: BiPy
# Bot Username : BiPy_Bot
bot_token = "Enter Bot Token here"
# Log into the telegram core: https://my.telegram.org
# Go to ‘API development tools’ and fill out the form.
# You will get the api_id and api_hash parameters required for user authorization.
# my phone number
phone = "Enter Phone Number Here"
api_id = 123456789  # API ID as integers
api_hash = "Enter API Hash Here"


# defines class coin
class Coin:
    def __init__(self, coin_name):
        self.name = coin_name.upper()
        self.dates = []
        self.close = []
        self.open = []
        self.high = []
        self.low = []
        self.volume = []
        self.current_price = 0.0
        self.buy_price = 0.0
        self.sell_price = 0.0
        self.coin_in_balance = False
        self.coin_balance = 0.0
        self.USDT_Balance = 0.0
        self.power = 0.0
        self.MA50 = []
        self.MA100 = []
        self.MA200 = []
        self.EMA50 = []
        self.EMA100 = []
        self.EMA200 = []
        self.MACD_line = []
        self.MACD_signal = []
        self.RSI = []
        self.lot_size_min_qty = 0
        self.minNotional = 0


def send_bot_message(passed_message):
    global bot_online
    if bot_online:
        try:
            bot.loop.run_until_complete(bot_main(passed_message))
        except (NameError, ConnectionError):
            pass


# define asyncio operation for telegram bot
async def bot_main(message_to_send):
    global bot_online
    if bot_online:
        # connecting and building the session
        await bot.connect()
        # sends message by username
        for user in users:
            try:
                await bot.send_message(user, message_to_send, parse_mode='html')
            except:
                pass


def download_coin_files(req_start_date, req_end_date, list_of_coins, interval="30m"):
    # gets coin data after end date and saves as CSV files
    count = 1
    for download_coin in list_of_coins:  # used to determine the coin required for action
        coin_name = download_coin.upper()
        print("#", str(str(count) + "/" + str(len(list_of_coins))), "Downloading", coin_name)
        coin_path = str("History CSV Files//" + download_coin + "_" + interval + ".csv")
        try:  # used to avoid errors when there is a coin with less than 1 day of history
            if path.exists(coin_path):
                loaded_data = pd.read_csv(coin_path, header=None)
                loaded_data = loaded_data.iloc[:-5]
                updated_start_date = dt.datetime.fromtimestamp(loaded_data[0][len(loaded_data[0]) - 1] / 1000) \
                                     + dt.timedelta(minutes=1)
                final_data = loaded_data
            else:
                print("New Coin")
                updated_start_date = req_start_date
                final_data = pd.DataFrame()
        except:
            print("New Coin")
            updated_start_date = req_start_date
            final_data = pd.DataFrame()
        # starts simulation at the end of fake data loaded
        step_start_date = updated_start_date
        # end data to ask the server
        step_end_date = step_start_date + dt.timedelta(minutes=3000)
        # gets data from server ands to CSV file every 1 day until 2021
        while step_start_date < req_end_date:
            # API url
            url = "https://api.binance.com/api/v3/klines"
            # converts start and end date to UNIX format for API
            start_time = str(int(step_start_date.timestamp() * 1000))
            end_time = str(int(step_end_date.timestamp() * 1000))
            # specify parameters to load
            req_params = {"symbol": coin_name, 'interval': interval, 'startTime': start_time, 'endTime': end_time}
            try:
                data = pd.DataFrame(json.loads(requests.get(url, params=req_params).text))
            except:
                time.sleep(10)
                data = pd.DataFrame(json.loads(requests.get(url, params=req_params).text))
            # gets only important data
            data = data.iloc[:, 0:6]
            # writes data to CSV
            # checks if results are empty
            if len(data.index) > 0:
                final_data = final_data.append(data)
            # incremental steps
            step_start_date = step_end_date + dt.timedelta(minutes=1)
            step_end_date = step_end_date + dt.timedelta(minutes=3000)
        # print final data to file
        final_data.drop_duplicates(subset=[0], keep="last")
        final_data = final_data.iloc[:-1]
        final_data.to_csv(str("History CSV Files//" + coin_name + "_" + interval + ".csv"), index=False, header=False, mode="w")
        # resets start datetime
        updated_start_date = req_start_date
        count = count + 1


# function to initialize coins investment rules
def initialization():
    print(str(dt.datetime.now().strftime("%b-%d, %H:%M")) + " update")
    # calls bot to send message
    message = str(dt.datetime.now().strftime("%b-%d, %H:%M")) + " update"
    send_bot_message(message)
    # Checks account balances
    balance_data = get_account_balance()
    # determines available USDT balance and number of coins in balance
    num_coins_in_balance = 0
    available_USDT_balance = 0
    portfolio_balance = 0
    last_BTC_price = 0
    transactions_PNL = 0
    current_coin_in_balance_buy_USDT = 0
    # loop through all items in balance
    for balance_item in balance_data:
        # loop through all coins
        for new_coin in gc.get_objects():
            if isinstance(new_coin, Coin):
                # checks if coin is in balance
                if (balance_item["asset"] + "USDT") == new_coin.name:
                    # determines last BTC price
                    if new_coin.name == "BTCUSDT":
                        last_BTC_price = new_coin.close[-1]
                    # checks if the remaining in balance is not movable
                    # accounts for BNB 25 USDT to account for fees
                    if (float(balance_item["free"]) * new_coin.close[-1] >= (10*1.01) and new_coin.name != "BNBUSDT") or\
                        (float(balance_item["free"]) * new_coin.close[-1] >= (25*1.01) and new_coin.name == "BNBUSDT"):
                        # counts the item as in balance
                        num_coins_in_balance = num_coins_in_balance + 1
                        new_coin.coin_in_balance = True
                        new_coin.coin_balance = float(balance_item["free"])
                        new_coin.USDT_Balance = 0
                        portfolio_balance = portfolio_balance + new_coin.coin_balance * new_coin.close[-1]
                        print("Coin in Balance", new_coin.name, new_coin.coin_balance, "PNL %:",
                              str(round(((new_coin.close[-1]-new_coin.buy_price)/new_coin.buy_price)*100, 2)))
                        # calls bot to send message
                        message = "Coin in Balance " + new_coin.name + " " + str(round(new_coin.coin_balance, 5)) + \
                                  " (PNL %: " + \
                                  str(round(((new_coin.close[-1]-new_coin.buy_price)/new_coin.buy_price)*100, 2)) + \
                                  ")"
                        send_bot_message(message)
                        current_coin_in_balance_buy_USDT = current_coin_in_balance_buy_USDT + \
                                                           new_coin.buy_price * new_coin.coin_balance
                        transactions_PNL = transactions_PNL + (new_coin.close[-1]*new_coin.coin_balance -
                                                               new_coin.buy_price*new_coin.coin_balance)
                    else:
                        new_coin.coin_in_balance = False
                        new_coin.buy_price = 0.0
        # updates USDT Balance
        if balance_item["asset"] == "USDT":
            available_USDT_balance = float(balance_item["free"])
    portfolio_balance = portfolio_balance + available_USDT_balance
    print("There are", num_coins_in_balance, "coins in balance")
    print("Current transactions PNL:", str(round(transactions_PNL, 2)), "USDT")
    print("Available USDT balance is:", available_USDT_balance)
    print("Current portfolio equivalent is:", str(round(portfolio_balance, 2)), "USDT")
    print("Current portfolio BTC equivalent is:", str(round(portfolio_balance/last_BTC_price, 4)), "BTC")
    # calls bot to send message
    message = "There are " + str(num_coins_in_balance) + " coins in balance"
    send_bot_message(message)
    message = "Current transactions PNL: " + str(round(transactions_PNL, 2)) + " USDT"
    send_bot_message(message)
    message = "Available USDT balance is: " + str(round(available_USDT_balance, 2))
    send_bot_message(message)
    message = "Current portfolio equivalent is: " + str(round(portfolio_balance, 2)) + " USDT"
    send_bot_message(message)
    message = "Current portfolio BTC equivalent is: " + str(round(portfolio_balance/last_BTC_price, 4)) + " BTC"
    send_bot_message(message)

    current_capital_equivalent = available_USDT_balance + current_coin_in_balance_buy_USDT
    capital_allocated_share = 0.1
    current_allocated_USDT = capital_allocated_share * current_capital_equivalent
    max_allocated_USDT = current_allocated_USDT / 20
    available_USDT_balance = current_allocated_USDT - current_coin_in_balance_buy_USDT
    print("Current Capital utilization:", str(round(capital_allocated_share*100, 2)), "%")
    # calls bot to send message
    message = "Current Capital utilization: " + str(round(capital_allocated_share*100, 2)) + "%"
    send_bot_message(message)
    print("Current Allocated Capital:", str(round(current_allocated_USDT, 2)), "USDT")
    # calls bot to send message
    message = "Current Allocated Capital: " + str(round(current_allocated_USDT, 2)) + " USDT"
    send_bot_message(message)
    print("Current Allocated USDT:", str(round(available_USDT_balance, 2)), "USDT")
    # calls bot to send message
    message = "Current Allocated USDT: " + str(round(available_USDT_balance, 2)) + " USDT"
    send_bot_message(message)

    # select coins to Allocate Capital to
    # list to store all coins powers
    all_coins_powers = []
    # loops through all coins
    for capital_coin in gc.get_objects():  # used to determine the coin required for update
        if isinstance(capital_coin, Coin) and capital_coin.name in required_coins:
            # check if coin history is more than 1 month
            if len(capital_coin.close) >= (2 * 24 * 30):
                # calculates coin power last 30 days
                capital_coin.power = capital_coin.close[-1] * sum(capital_coin.volume[-2 * 24:-1])
                all_coins_powers.append(capital_coin.power)
            else:
                capital_coin.power = 0
    # sorts the all coins powers in descending order
    all_coins_powers.sort(reverse=True)
    # defines the power limit for coins to invest in (Invest on only in top 10% of coins)
    if len(all_coins_powers) > 1:
        # limits the maximum coins to 20 coins
        if math.ceil(0.1 * len(all_coins_powers)) > 19:
            limit = 19
        else:
            limit = math.ceil(0.1 * len(all_coins_powers))
        power_limit = all_coins_powers[limit]
    # corrects for 1 coin only investment
    else:
        power_limit = all_coins_powers[0]
    # counts the number of coins exceeding the power limit
    coins_count = len([power for power in all_coins_powers if power >= power_limit])
    print("Plan to invest in:", coins_count, "coins")
    # calls bot to send message
    message = "Plan to invest in: " + str(coins_count) + " coins"
    send_bot_message(message)
    # checks number of coins for investment
    coins_for_investment = coins_count - num_coins_in_balance

    # only assigns USDT if coins for investment > 0
    if coins_for_investment != 0:
        # initialize coins USDT balance if there is no sufficient balance
        coins_USDT_balance = -1
        if (available_USDT_balance / coins_for_investment) <= (10*1.01):
            # if there is not enough USDT Balance for any investment < 10
            if available_USDT_balance < (10*1.01):
                print("There is not enough USDT balance for any investment")
                # calls bot to send message
                message = "There is not enough USDT balance for any investment"
                send_bot_message(message)
                # assigns 0 USDT balance for all coins
                coins_USDT_balance = 0.0
            # if there is only enough investment for 1 coin (USDT Balance < 20)
            elif available_USDT_balance <= 2 * (10*1.01):
                print("There is enough USDT balance for investment in 1 coin only")
                # calls bot to send message
                message = "There is enough USDT balance for investment in 1 coin only"
                send_bot_message(message)
                coins_USDT_balance = available_USDT_balance
            # if there is only enough investment for more than 1 coin but not all coins
            elif available_USDT_balance - int(math.floor(available_USDT_balance / (10*1.01)))*(10*1.01) \
                    <= coins_for_investment * (10*1.01):
                print("There is enough USDT balance for investment in more than 1 coin but not all selected coins")
                # calls bot to send message
                message = "There is enough USDT balance for investment in more than 1 coin but not all selected coins"
                send_bot_message(message)
                max_num_coins = math.floor(available_USDT_balance / (10*1.01))
                coins_USDT_balance = (10*1.01) + (available_USDT_balance - (max_num_coins * 10*1.01))/max_num_coins
        # assigns available USDT balance to coins not in balance and above power limit
        for new_coin in gc.get_objects():
            if isinstance(new_coin, Coin):
                # checks if there is no sufficient balance to cover all coins
                if (coins_USDT_balance != -1) and (not new_coin.coin_in_balance) and (new_coin.power >= power_limit):
                    # used 1% margin for delays in buy and sell and market price
                    new_coin.USDT_Balance = 0.99 * coins_USDT_balance
                # if coin is not in balance and coin power > power limit and there is enough USDT to cover all coins
                elif (not new_coin.coin_in_balance) and (new_coin.power >= power_limit):
                    # defines maximum allocated USDT to avoid errors with human intervention
                    if (available_USDT_balance / coins_for_investment) > max_allocated_USDT:
                        # used 1% margin for delays in buy and sell and market price
                        new_coin.USDT_Balance = 0.99 * max_allocated_USDT
                    else:
                        # used 1% margin for delays in buy and sell and market price
                        new_coin.USDT_Balance = 0.99 * available_USDT_balance / coins_for_investment
                else:
                    new_coin.USDT_Balance = 0
    else:
        # assigns 0 USDT to all coins if coins in balance = coins for investment
        for new_coin in gc.get_objects():
            if isinstance(new_coin, Coin):
                new_coin.USDT_Balance = 0


# restarts Websocket connection
def ws_connect():
    global ws_url
    # establishes Websocket connection
    ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message, on_close=on_close, on_error=on_error)
    # used for restarting websocket
    ws.close()
    # makes websocket run forever
    ws.run_forever()


# creates Websocket connection
def ws_restart():
    global ws_url
    # establishes Websocket connection
    ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message, on_close=on_close, on_error=on_error)
    # used for restarting websocket
    ws.close()
    print("Websocket Closed to save internet usage")
    # calls bot to send message
    message = "Websocket Closed to save internet usage"
    send_bot_message(message)
    # stops the App to save internet usage
    time.sleep(27*60)
    # sync Computer time
    try:
        os.system('w32tm /resync')
        print("Time Sync'ed to Binance API")
        # calls bot to send message
        message = "Time Sync'ed to Binance API"
        send_bot_message(message)
    except:
        pass
    # makes websocket run forever
    ws.run_forever()


# used to get account info for trading
def get_account_balance():
    account_client = Client(API_Key, API_Secret)
    # used to correct for difference in time between pc and server
    updated_account_info = account_client.get_account(recvWindow=60000)
    return updated_account_info["balances"]


# used to make orders
def make_order(side, symbol, quantity, order_type=ORDER_TYPE_MARKET):
    try:
        # function used to make an order (buy or sell)
        # symbol e.g. BTCUSDT, quantity e.g. 10, side = "SIDE_SELL" or "SIDE_BUY"
        # order_type e.g. (LIMIT, MARKET, STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, TAKE_PROFIT_LIMIT, LIMIT_MAKER
        # order type and side MUST BE ALL CAPS
        print("Sending order")
        order = client.create_order(symbol=symbol, quantity=quantity, side=side, type=order_type, recvWindow=60000)
        print(order)
        return "Order Succeeded"
    except Exception as e:
        print(e)
        return "Order Failed"


# defines message received from server
def on_message(ws, incoming_message):
    json_message = json.loads(incoming_message)  # loads message into JSON format
    stream = json_message["stream"]  # defines which coin stream is received
    candle = json_message["data"]["k"]  # gets candle data only from JSON object
    message_operations(stream, candle)


# define actions on close from server
def on_close(ws):
    print("Connection Closed")
    # calls bot to send message
    message = "Connection Closed"
    send_bot_message(message)
    # delay 15 seconds
    time.sleep(15)
    # connect to websocket
    ws_connect()


# define actions on open from server
def on_open(ws):
    print("Connection Started (Restarted)")
    # calls bot to send message
    message = "Connection Started (Restarted)"
    send_bot_message(message)


# define actions on error from server
def on_error(ws, e):
    print(e)
    # calls bot to send message
    message = e
    send_bot_message(message)


# makes main logic operations every message
def message_operations(stream, candle):
    # calculates time since last update
    global last_update
    last_update_since = dt.datetime.now() - last_update
    # check if its 1 or 31 minutes to update user
    if dt.datetime.now().minute == 1 or dt.datetime.now().minute == 31:
        # calls initialization function to define powers and actualize investments
        initialization()
        # update last update time
        last_update = dt.datetime.now()
        # restarts websocket for refreshing connection and stops Websocket for 28 minutes to save internet usage
        ws_restart()
    # updates main coin data
    coin_name = stream[:stream.find("@")]  # returns only coin name from stream
    for update_coin in gc.get_objects():  # used to determine the coin required for update
        if isinstance(update_coin, Coin) and update_coin.name.lower() == coin_name:
            last_30m_update = dt.datetime.now()
            update_coin.current_price = float(candle["c"])  # assigns current price to Each coin object
            # checks if candle is closed
            is_candle_closed = candle["x"]
            # if to add closing prices if candle is closed
            if is_candle_closed:
                # update coin database
                update_coin.dates.append(dt.datetime.fromtimestamp(float(candle["T"])/1000))  # converts date from UNIX
                update_coin.close.append(float(candle["c"]))  # converts close price to float
                update_coin.open.append(float(candle["o"]))  # converts open price to float
                update_coin.high.append(float(candle["h"]))  # converts high price to float
                update_coin.low.append(float(candle["l"]))  # converts low price to float
                update_coin.volume.append(float(candle["v"]))  # converts volume to float
                # update moving average indicators
                update_coin.MA50 = pd.Series(update_coin.close).rolling(window=50).mean().astype("float").tolist()
                update_coin.M100 = pd.Series(update_coin.close).rolling(window=100).mean().astype("float").tolist()
                update_coin.M200 = pd.Series(update_coin.close).rolling(window=200).mean().astype("float").tolist()
                update_coin.EMA50 = ta_trend.ema_indicator(pd.Series(update_coin.close), 50).astype("float").tolist()
                update_coin.EMA100 = ta_trend.ema_indicator(pd.Series(update_coin.close), 100).astype("float").tolist()
                update_coin.EMA200 = ta_trend.ema_indicator(pd.Series(update_coin.close), 200).astype("float").tolist()
                update_coin.MACD_line = ta_trend.macd(pd.Series(update_coin.close), 26, 12).astype("float")
                update_coin.MACD_signal = ta_trend.macd_signal(pd.Series(update_coin.close), 26, 12).astype("float")
                update_coin.RSI = ta_momentum.rsi(pd.Series(update_coin.close), 14).astype("float")
                # Decisions
                if update_coin.coin_in_balance or update_coin.USDT_Balance > 0:
                    print(dt.datetime.now(), update_coin.name, "30m closing price is",
                          str(round(float(candle["c"]), 5)), "Buy Price:", str(round(float(update_coin.buy_price), 4)))
                    # calls bot to send message
                    message = update_coin.name + " 30m closing price is: " + \
                              str(round(float(candle["c"]), 5)) + ", Buy Price: " + \
                              str(round(float(update_coin.buy_price), 5))
                    send_bot_message(message)
                # Decide actions based on indicators
                buy = False
                sell = False
                # if Coin is not in Balance Buy and USDT > 0
                if (update_coin.MACD_line[-1] >= update_coin.MACD_signal[-1]) and \
                        (update_coin.MACD_line[-2] < update_coin.MACD_signal[-2]) and \
                        (not update_coin.coin_in_balance) and update_coin.USDT_Balance > 0:
                    buy = True
                    sell = False
                # if coin in balance
                if (update_coin.MACD_line[-1] < update_coin.MACD_signal[-1]) and update_coin.coin_in_balance:
                    sell = True
                    buy = False
                # executes buy decisions
                if buy and update_coin.USDT_Balance > 0:
                    # calculates current quantity of coins to buy
                    buy_qty = update_coin.USDT_Balance / update_coin.current_price
                    # updates buy price
                    update_coin.buy_price = update_coin.current_price
                    if update_coin.lot_size_min_qty >= 1:
                        buy_qty = int(math.floor(buy_qty))
                    else:
                        min_qty_decimals = int(-math.log10(abs(update_coin.lot_size_min_qty)))
                        buy_qty = str(round(buy_qty, min_qty_decimals))
                    # prints order
                    print("Order is buy", update_coin.name, "by", str(round(update_coin.USDT_Balance, 3)), "USDT")
                    # calls bot to send message
                    message = "Order is buy " + update_coin.name + " by " + str(round(update_coin.USDT_Balance, 3)) + " USDT"
                    send_bot_message(message)
                    # makes order and prints results
                    order = make_order(SIDE_BUY, update_coin.name, str(buy_qty))
                    print(order)
                    # retry if failed
                    order_try_count = 1
                    while (order != "Order Succeeded") and order_try_count <= 3:
                        print("retrying order")
                        order = make_order(SIDE_BUY, update_coin.name, str(buy_qty))
                        print(order)
                        order_try_count = order_try_count + 1
                    # calls bot to send message
                    message = order
                    send_bot_message(message)
                    # updates coin information
                    if order == "Order Succeeded":
                        update_coin.coin_in_balance = True
                        update_coin.coin_balance = buy_qty * 0.999  # 0.1% Binance fess
                        update_coin.USDT_Balance = 0.0
                # executes sell decisions
                if sell and update_coin.coin_balance > 0:
                    # checks the minimum quantity for buy and sell
                    if update_coin.lot_size_min_qty >= 1:
                        sell_qty = int(math.floor(update_coin.coin_balance))
                    else:
                        min_qty_decimals = int(-math.log10(abs(update_coin.lot_size_min_qty)))
                        factor = 1 / (10 ** min_qty_decimals)
                        # leaves 20 USDT BNB to avoid errors and to be used in buy and sell fees
                        if update_coin.name == "BNBUSDT":
                            BNB_sell_balance = update_coin.coin_balance - (20 / update_coin.close[-1])
                            sell_qty = (BNB_sell_balance // factor) * factor
                            sell_qty = str(round(sell_qty, min_qty_decimals))
                        else:
                            sell_qty = (update_coin.coin_balance // factor) * factor
                            sell_qty = str(round(sell_qty, min_qty_decimals))
                    print("Order is sell", sell_qty, update_coin.name)
                    # calls bot to send message
                    message = "Order is sell " + str(sell_qty) + " " + update_coin.name
                    send_bot_message(message)
                    order = make_order(SIDE_SELL, update_coin.name, sell_qty)
                    print(order)
                    # retry if failed
                    order_try_count = 1
                    while (order != "Order Succeeded") and order_try_count <= 3:
                        print("retrying order")
                        order = make_order(SIDE_SELL, update_coin.name, str(sell_qty))
                        print(order)
                        order_try_count = order_try_count +1
                    # calls bot to send message
                    message = order
                    send_bot_message(message)
                    # updates coin information
                    if order == "Order Succeeded":
                        update_coin.coin_in_balance = False
                        update_coin.USDT_Balance = 0.0
                        update_coin.coin_balance = 0.0
                        update_coin.buy_price = 0.0


##############################
# initialize and start running
required_interval = "30m"  # defines required interval

# connecting to Binance
client = Client(API_Key, API_Secret)

# creating a telegram session
# We have to manually call "start" if we want an explicit bot token
try:
    bot = TelegramClient("BiPy_Bot", api_id, api_hash).start(bot_token=bot_token)
    bot_online = True
except (ConnectionError, TimeoutError):
    bot_online = False
    print("Telegram bot offline")

# list of usernames to send messages to
users = ["user1", "user2"]

print("BiPy Live Project started")
# calls bot to send message
message = "BiPy Live Project started"
send_bot_message(message)

# defines required coins
required_coins = []
url = "https://api3.binance.com/api/v3/exchangeInfo"
exchange_info = json.loads(requests.get(url).text)
for symbol_data in exchange_info["symbols"]:
    if symbol_data["quoteAsset"] == "USDT":  # for only trading against USDT
        if symbol_data["status"] == "TRADING":  # to cancel coins that stopped trading
            # Remove Fiat (real currencies from downloaded coins
            if ("USD" not in symbol_data["symbol"][:-4]) and ("AUD" not in symbol_data["symbol"][:-4]) \
                    and ("EUR" not in symbol_data["symbol"][:-4]) and ("GBP" not in symbol_data["symbol"][:-4]) \
                    and ("PAX" not in symbol_data["symbol"][:-4]):  # cancel other fiat
                # Remove short & long coins (UP & DOWN)
                if "UP" not in symbol_data["symbol"][:-4] and "DOWN" not in symbol_data["symbol"][:-4]:
                    required_coins.append(symbol_data["symbol"])
print("There are", len(required_coins), "coins trading on Binance")


# updates downloaded history files
download_start_date = dt.datetime(2021, 6, 1)  # remember to update to reduce time lost in new coins
download_end_date = dt.datetime.now()
download_coin_files(download_start_date, download_end_date, required_coins, required_interval)
print("Coins history Downloaded/Updated")
# calls bot to send message
message = "Coins history Downloaded/Updated"
send_bot_message(message)


# count of downloaded items
download_count = 1
# download historical data
for load_coin in required_coins:
    # reads history file
    try:
        data = pd.read_csv(str("History CSV Files//" + load_coin + "_" + "30m" + ".csv"), header=None)
        data.columns = ["UNIX_Datetime", "open", "high", "low", "close", "volume"]
    except FileNotFoundError:
        continue
    # cancels just released coins in last 24 hours
    if len(data.index) <= 24*2:
        continue
    # creates the new coin
    vars()[load_coin] = Coin(load_coin)
    # checks the length of coins history and changes start point to reduce RAM load
    loading_start = 0
    if len(data.index) <= 24*30*2:  # last month
        loading_start = 0
    else:
        loading_start = len(data.index) - 24*30*2  # last month
    # assigns data to coins
    for row in range(loading_start, len(data.index)):
        vars()[load_coin].dates.append(dt.datetime.fromtimestamp(float(data["UNIX_Datetime"][row]) / 1000))
        vars()[load_coin].open.append(float(data["open"][row]))
        vars()[load_coin].high.append(float(data["high"][row]))
        vars()[load_coin].low.append(float(data["low"][row]))
        vars()[load_coin].close.append(float(data["close"][row]))
        vars()[load_coin].volume.append(float(data["volume"][row]))
    print(vars()[load_coin].name, "Last close", vars()[load_coin].close[-1])
    print(str(str(download_count) + "/" + str(len(required_coins))), vars()[load_coin].name, "History loaded")
    # checks how many coins are downloaded
    download_count = download_count + 1
print("Coins history loaded")
# calls bot to send message
message = "Coins history loaded"
send_bot_message(message)

filters_count = 1
# creates required trading filters
for filter_coin in gc.get_objects():
    if isinstance(filter_coin, Coin):
        print("Loading", str(str(filters_count) + "/" + str(len(required_coins))), filter_coin.name, "filters")
        filter_data = True
        while filter_data:
            try:
                coin_filters = client.get_symbol_info(filter_coin.name)
                filter_data = False
            except:
                filter_data = True
                # used to avoid bans
                time.sleep(0.5)
        # possible filters
        # PRICE_FILTER, PERCENT_PRICE, LOT_SIZE, MIN_NOTIONAL
        # defines minimum trading quantity for each coin
        filter_coin.lot_size_min_qty = float(coin_filters["filters"][2]["minQty"])
        # defines minimum notional
        filter_coin.minNotional = float(coin_filters["filters"][3]["minNotional"])
        # used to avoid bans
        time.sleep(0.25)
        filters_count = filters_count + 1
print("Coins filters loaded")
# calls bot to send message
message = "Coins filters loaded"
send_bot_message(message)

# updates last buy price
orders_count = 1
for price_coin in gc.get_objects():
    if isinstance(price_coin, Coin):
        order_data = True
        orders = []
        print("Loading", str(str(orders_count) + "/" + str(len(required_coins))), price_coin.name, "Orders")
        while order_data:
            try:
                orders = client.get_all_orders(symbol=price_coin.name, recvWindow=60000)
                order_data = False
            except:
                order_data = True
                print("Error in orders")
                # used to avoid bans
                time.sleep(0.5)
        last_order_id = 0
        price_coin.buy_price = 0
        for order in orders:
            if float(order["orderId"]) > last_order_id:
                if order["side"] == "BUY":
                    last_order_id = float(order["orderId"])
                    price_coin.buy_price = float(order["cummulativeQuoteQty"]) / float(order["origQty"])
        # used to avoid bans
        time.sleep(0.25)
        orders_count = orders_count + 1
print("Coins orders loaded")
# calls bot to send message
message = "Coins orders loaded"
send_bot_message(message)

print(str(len(required_coins)) + " Coins history loaded")
# calls bot to send message
message = str(len(required_coins)) + " Coins history loaded"
send_bot_message(message)

# run initialization function
initialization()
last_update = dt.datetime.now()

# define the base combined streams url
base_ws_url = "wss://stream.binance.com:9443/stream?streams="
# loops through all coins to create the combined streams url
coins_ws_url = ""
for coin_stream in required_coins:
    coins_ws_url = coins_ws_url + coin_stream.lower() + "@kline_" + required_interval + "/"
# removes last letter (/) from coins_ws_url
coins_ws_url = coins_ws_url[:-1]
# url for Websocket
ws_url = (base_ws_url + coins_ws_url)
# Connect to Websocket
ws_connect()
