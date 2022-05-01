# references
# Websocket in Binance https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md
# Binance Python API https://python-binance.readthedocs.io/en/latest/
# other Binance Websocket https://python-binance.readthedocs.io/en/latest/websockets.html
# Telegram bot # https://docs.telethon.dev/en/latest/basic/quick-start.html

# pip install websocket-client
import gc  # used to get all coin objects
import websocket  # used to send and receive live data
import json  # used to get received data
# You MUST manually run/install twisted file
# pip install python-binance
from binance.client import Client  # used to connect to Binance
# from binance.enums import *  # used to get buy and sell signals
import pandas as pd  # used for data manipulation
import datetime as dt  # used for datetime
import requests  # used for API history loading
import math  # used for rounding
from ta import trend as ta_trend  # used to calculate the different trend indicators
from ta import momentum as ta_momentum  # used to calculate the different momentum indicators
import websocket  # used to send and receive live data
import time  # used for delay during re-connection
# pip install telethon
from telethon import TelegramClient  # used for Telegram bot
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


# define a asyncio operation for telegram bot
async def bot_main(message_to_send):
    # connecting and building the session
    await bot.connect()
    # sends message by username
    for user in users:
        await bot.send_message(user, message_to_send, parse_mode='html')


# creates Websocket connection
def ws_connect():
    global ws_url
    # establishes Websocket connection
    ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message, on_close=on_close, on_error=on_error)
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
    bot.loop.run_until_complete(bot_main(message))
    # stops the App to save internet usage
    time.sleep(27*60)
    # sync Computer time
    try:
        os.system('w32tm /resync')
        print("Time Sync'ed to Binance API")
        # calls bot to send message
        message = "Time Sync'ed to Binance API"
        bot.loop.run_until_complete(bot_main(message))
    except:
        pass
    # makes websocket run for ever
    ws.run_forever()


# defines message received from server
def on_message(ws, incoming_message):
    json_message = json.loads(incoming_message)  # loads message into JSON format
    stream = json_message["stream"]  # defines which coin stream is received
    candle = json_message["data"]["k"]  # gets candle data only from JSON object
    message_operations(stream, candle)


# Define actions on close from server
def on_close(ws):
    print("Connection Closed")
    # calls bot to send message
    message = "Connection Closed"
    bot.loop.run_until_complete(bot_main(message))
    # delay 15 seconds
    time.sleep(15)
    # connect to websocket
    ws_connect()


# Define actions on open from server
def on_open(ws):
    print("Connection Started")
    # calls bot to send message
    message = "Connection Started"
    bot.loop.run_until_complete(bot_main(message))


# Define actions on error from server
def on_error(ws, e):
    print(e)
    # calls bot to send message
    message = e
    bot.loop.run_until_complete(bot_main(message))


# function to initialize coins investment rules
def initialization():
    print(str(dt.datetime.now().strftime("%b-%d, %H:%M")) + " update")
    # calls bot to send message
    message = str(dt.datetime.now().strftime("%b-%d, %H:%M")) + " update"
    bot.loop.run_until_complete(bot_main(message))
    # Checks account balances
    balance_data = fake_get_account_balance()
    # determines available USDT balance and number of coins in balance
    num_coins_in_balance = 0
    available_USDT_balance = 0
    portfolio_balance = 0
    # loop through all items in balance
    for balance_item in balance_data:
        # loop through all coins
        for new_coin in gc.get_objects():
            if isinstance(new_coin, Coin):
                # checks if coin is in balance
                if balance_item["asset"] == new_coin.name:
                    # counts the item as in balance
                    num_coins_in_balance = num_coins_in_balance + 1
                    new_coin.coin_in_balance = True
                    new_coin.coin_balance = balance_item["free"]
                    new_coin.USDT_Balance = 0
                    portfolio_balance = portfolio_balance + new_coin.coin_balance * new_coin.close[-1]
                    print("Coin in Balance", new_coin.name, new_coin.coin_balance)

                    # calls bot to send message
                    message = "Coin in Balance " + new_coin.name + " " + str(round(new_coin.coin_balance, 2))
                    bot.loop.run_until_complete(bot_main(message))

        # updates USDT Balance
        if balance_item["asset"] == "USDT":
            available_USDT_balance = balance_item["free"]

    portfolio_balance = portfolio_balance + available_USDT_balance
    print("There are", num_coins_in_balance, "coins in balance")
    print("Available USDT balance is:", available_USDT_balance)
    print("Current portfolio equivalent is:", str(round(portfolio_balance, 2)), "USDT")

    # calls bot to send message
    message = "There are " + str(num_coins_in_balance) + " coins in balance"
    bot.loop.run_until_complete(bot_main(message))
    message = "Available USDT balance is: " + str(round(available_USDT_balance, 2))
    bot.loop.run_until_complete(bot_main(message))
    message = "Current portfolio equivalent is: " + str(round(portfolio_balance, 2)) + " USDT"
    bot.loop.run_until_complete(bot_main(message))

    # select coins to Allocate Capital to
    # list to store all coins powers
    all_coins_powers = []
    # loops through all coins
    for capital_coin in gc.get_objects():  # used to determine the coin required for update
        if isinstance(capital_coin, Coin) and capital_coin.name in required_coins:
            # ensures coin have been trading for at least 2 months
            if len(capital_coin.close[:-1]) > (2 * 24 * 3):
                # calculates coin power
                # this method use previous close * sum of volume last 24 hours
                capital_coin.power = capital_coin.close[-1] * sum(capital_coin.volume[-2 * 24:-1])
                all_coins_powers.append(capital_coin.power)
            else:
                capital_coin.power = 0
    # sorts the all coins powers in descending order
    all_coins_powers.sort(reverse=True)
    # defines the power limit for coins to invest in (Invest on only in top 10% of coins)
    power_limit = all_coins_powers[math.ceil(0.10 * len(all_coins_powers))]
    # counts the number of coins exceeding the power limit
    coins_count = len([power for power in all_coins_powers if power >= power_limit])
    print("Plan to invest in:", coins_count, "coins")
    # calls bot to send message
    message = "Plan to invest in: " + str(coins_count) + " coins"
    bot.loop.run_until_complete(bot_main(message))

    # assigns available USDT balances to each coin not in balance and above power limit
    for new_coin in gc.get_objects():
        if isinstance(new_coin, Coin):
            # if coin is not in balance and coin power > power limit
            if (not new_coin.coin_in_balance) and (new_coin.power >= power_limit):
                # used 2% margin for delays in buy and sell and market price
                new_coin.USDT_Balance = 0.98 * available_USDT_balance / (coins_count - num_coins_in_balance)
            else:
                new_coin.USDT_Balance = 0


# used to get fake account info to test the code
def fake_get_account_balance():
    account_data = pd.read_csv("My_fake_account_info.csv", header=0)
    latest_info = []
    for ind in range(0, len(account_data)):
        account_item = {"asset": account_data["asset"][ind], "free": account_data["free"][ind],
                        "locked": account_data["locked"][ind]}
        latest_info.append(account_item)
    return latest_info


# used to make fake orders to test the code
def fake_make_orders(side, symbol, quantity):
    required_USDT = 0.0
    current_coin_price = 0.0
    # function to get market price
    for action_coin in gc.get_objects():  # used to determine the coin required for action
        if isinstance(action_coin, Coin) and action_coin.name == symbol:
            current_coin_price = action_coin.current_price  # used to get the current coin price
            required_USDT = quantity * current_coin_price  # used to get the required USDT
    if side == "SIDE_SELL":
        # loads account_balance for changing
        data = pd.read_csv("My_fake_account_info.csv", header=0)
        USDT_index = 0
        symbol_index = 0
        for idx in range(0, len(data)):
            if data.loc[idx, "asset"] == symbol:
                symbol_index = idx
            # searches for USDT to update balance
            elif data.loc[idx, "asset"] == "USDT":
                USDT_index = idx
        # calculates previous USDT balance
        previous_USDT_balance = float(data.loc[USDT_index, "free"])
        # deletes old USDT row
        data = data.drop([USDT_index])
        # deletes symbol row
        data = data.drop([symbol_index])
        # updates USDT balance
        updated_USDT_Balance = previous_USDT_balance + required_USDT
        new_data = pd.DataFrame({"asset": ["USDT"], "free": [updated_USDT_Balance], "locked": [0]})
        data = pd.concat([data, new_data])
        # updates fake account info
        data.to_csv("My_fake_account_info.csv", index=False)
    elif side == "SIDE_BUY":
        # loads account_balance for changing
        data = pd.read_csv("My_fake_account_info.csv", header=0)
        USDT_index = 0
        for idx in range(0, len(data)):
            # searches for USDT to update balance
            if data.loc[idx, "asset"] == "USDT":
                USDT_index = int(idx)
        # calculates previous USDT balance
        previous_USDT_balance = data[USDT_index, "free"]
        # updates previous USDT balance
        updated_USDT_Balance = previous_USDT_balance - required_USDT
        # deletes old USDT row
        data = data.drop([USDT_index])
        # updates USDT balance
        new_data = pd.DataFrame({"asset": ["USDT"], "free": [updated_USDT_Balance], "locked": [0]})
        data = pd.concat([data, new_data])
        # updates coin quantity
        updated_coin_balance = quantity
        new_data = pd.DataFrame({"asset": [symbol], "free": [updated_coin_balance], "locked": [0]})
        data = pd.concat([data, new_data])
        # updates fake account info
        data.to_csv("My_fake_account_info.csv", index=False)
    # used to update transaction log for tracking
    update_transaction_log = pd.DataFrame({"datetime": dt.datetime.now(), "asset": [symbol],
                                           "operation": side, "quantity": quantity,
                                           "price": current_coin_price})
    update_transaction_log.to_csv("My_fake_transaction_log.csv", index=False, mode="a", header=False)
    return str("Order succeeded")


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
                if update_coin.coin_in_balance or update_coin.USDT_Balance > 0:
                    print(dt.datetime.now(), update_coin.name, "30m closing price is {}"
                          .format(round(float(candle["c"]), 3)))
                    # calls bot to send message
                    message = update_coin.name + " 30m closing price is {}".format(round(float(candle["c"]), 3))
                    bot.loop.run_until_complete(bot_main(message))
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
                if buy:
                    # calculates current quantity of coins to buy
                    coin_quantity = update_coin.USDT_Balance / update_coin.current_price
                    # prints order
                    print("Order is buy", update_coin.name, "by", str(round(update_coin.USDT_Balance, 2)), "USDT")
                    # calls bot to send message
                    message = "Order is buy {} by {} USDT".format(update_coin.name, round(update_coin.USDT_Balance, 2))
                    bot.loop.run_until_complete(bot_main(message))
                    # makes order and prints results
                    order = fake_make_orders("SIDE_BUY", update_coin.name, coin_quantity)
                    print(order)
                    # calls bot to send message
                    message = order
                    bot.loop.run_until_complete(bot_main(message))
                    # updates coin information
                    update_coin.coin_in_balance = True
                    update_coin.coin_balance = coin_quantity * 0.999  # 0.1% Binance fess
                    update_coin.USDT_Balance = 0.0
                # executes sell decisions
                if sell:
                    print("Order is sell", update_coin.coin_balance, update_coin.name)
                    # calls bot to send message
                    message = "Order is sell {} {}".format(round(update_coin.coin_balance, 4), update_coin.name)
                    bot.loop.run_until_complete(bot_main(message))
                    order = fake_make_orders("SIDE_SELL", update_coin.name, update_coin.coin_balance)
                    print(order)
                    # calls bot to send message
                    message = order
                    bot.loop.run_until_complete(bot_main(message))
                    # updates coin information
                    update_coin.coin_in_balance = False
                    update_coin.USDT_Balance = 0.0
                    update_coin.coin_balance = 0.0


##############################
# initialize and start running
required_interval = "30m"  # defines required interval

# connecting to Binance
client = Client(API_Key, API_Secret)

# creating a telegram session
# We have to manually call "start" if we want an explicit bot token
bot = TelegramClient("BiPy_Bot", api_id, api_hash).start(bot_token=bot_token)

# list of usernames to send messages to
users = ["user1", "user2"]

print("BiPy testing project started")
# calls bot to send message
message = "BiPy testing project started"
bot.loop.run_until_complete(bot_main(message))

# list of all available coins
required_coins = []
binance_url = "https://api3.binance.com/api/v3/exchangeInfo"
exchange_info = json.loads(requests.get(binance_url).text)
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

# count of downloaded items
download_count = 1
# download historical data
for download_coin in required_coins:
    vars()[download_coin] = Coin(download_coin)
    # Gets historical data for each coin you may change start_str="1 Dec, 2017"
    hist_candles = client.get_historical_klines(vars()[download_coin].name, start_str="5 days ago UTC",
                                                interval=required_interval)
    for hist_candle in hist_candles:
        vars()[download_coin].dates.append(dt.datetime.fromtimestamp(float(hist_candle[6]) / 1000))
        vars()[download_coin].open.append(float(hist_candle[1]))
        vars()[download_coin].high.append(float(hist_candle[2]))
        vars()[download_coin].low.append(float(hist_candle[3]))
        vars()[download_coin].close.append(float(hist_candle[4]))
        vars()[download_coin].volume.append(float(hist_candle[5]))
    print(str(str(download_count) + "/" + str(len(required_coins))), vars()[download_coin].name, "History loaded")
    download_count = download_count + 1

# calls bot to send message
message = "{} Coins history loaded".format(len(required_coins))
bot.loop.run_until_complete(bot_main(message))

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

# connect on websocket
ws_connect()
