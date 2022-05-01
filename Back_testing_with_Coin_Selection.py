from ta import trend as ta_trend  # used to calculate the different trend indicators
import pandas as pd  # used for data manipulation
import datetime as dt  # used for datetime
import gc
import json  # used to get received data
import requests  # used for API history loading
import matplotlib.pyplot as plt  # used for plotting
import math  # used for rounding
import numpy as np
from ta import momentum as ta_momentum  # used to calculate the different momentum indicators


# defines class coin
class Coin:
    def __init__(self, coin_name):
        self.name = coin_name.upper()
        self.data = pd.DataFrame()
        self.power = 0
        self.transactions = 0
        self.coin_in_balance = False
        self.coin_balance = 0.0
        self.USDT_Balance = 0
        self.buy_date = 0
        self.last_buy_price = 0.0
        self.time_since_buy = 0
        self.MA50 = []
        self.EMA50 = []


# defines interval
interval = "30m"
# define Investment
investment_USDT = 100
# defines start and end dates
start_date = dt.datetime.strptime("01-12-2021 00:00:00", "%d-%m-%Y %H:%M:%S")  # remember to shift 30m before
current_date = start_date
end_date = dt.datetime.strptime("01-01-2022 12:00:00", "%d-%m-%Y %H:%M:%S")  # remember to shift 30m before


# list of all available coins
list_all_coins = []
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
                    list_all_coins.append(symbol_data["symbol"])
print("There are", len(list_all_coins), "coins trading on Binance")
# used to avoid error signals when Market is closed
BNBUSDT = Coin("BNBUSDT")

# read history files
for fake_coin in list_all_coins:  # used to determine the coin required for action
    # load first day as history into coin
    try:
        data = pd.read_csv(str("History CSV Files//" + fake_coin + "_" + interval + ".csv"), header=None)
    except FileNotFoundError:
        continue
    data.columns = ["UNIX_Datetime", "open", "high", "low", "close", "volume"]
    data.index = [dt.datetime.fromtimestamp(x / 1000.0) for x in data["UNIX_Datetime"]]
    # Calculates moving average indicators
    data['MA50'] = data["close"].rolling(window=50).mean().astype("float")
    data['MA100'] = data["close"].rolling(window=100).mean().astype("float")
    data['MA200'] = data["close"].rolling(window=200).mean().astype("float")
    # Calculates Exponential moving average indicators
    data["EMA50"] = ta_trend.ema_indicator(pd.Series(data["close"]), 50).astype("float")
    data["EMA100"] = ta_trend.ema_indicator(pd.Series(data["close"]), 100).astype("float")
    data["EMA200"] = ta_trend.ema_indicator(pd.Series(data["close"]), 200).astype("float")
    # Calculates MACD
    data["MACD_line"] = ta_trend.macd(pd.Series(data["close"]), 26, 12).astype("float")
    data["MACD_signal"] = ta_trend.macd_signal(pd.Series(data["close"]), 26, 12, 9).astype("float")
    # Calculates RSI
    data["RSI"] = ta_momentum.rsi(pd.Series(data["close"]), 14).astype("float")
    # end of calculations
    # creates class coin for required coins
    vars()[fake_coin] = Coin(fake_coin)  # creates new coin
    vars()[fake_coin].data = data
    print(vars()[fake_coin].name, "History loaded")


# Variables to store results
my_portfolio_profile = []
my_portfolio_profile_change = []  # used to store change ratio
my_portfolio_profile_dates = []
pos_transactions_net = []
pos_transactions_net_change = []  # used to store change ratio
neg_transactions_net = []
neg_transactions_net_change = []  # used to store change ratio

# Initialize Variables
my_new_portfolio = 0
current_USDT_balance = investment_USDT
start_day_portfolio = investment_USDT
daily_portfolio = [investment_USDT]  # initializes first day
daily_portfolio_dates = [start_date]
holding_time_list = []

# main loop
while current_date <= end_date:
    # used to check if Market is closed via BNB
    try:
        BNBUSDT.data["close"][current_date]
    except KeyError:
        print("Market Closed -", current_date)
        current_date = current_date + dt.timedelta(minutes=30)
        continue
    # list of coins in balance
    coins_in_balance_list = []
    my_new_portfolio = 0
    coins_in_balance = 0
    # defines all coins powers
    all_power = []
    for update_coin in gc.get_objects():  # used to determine the coin required for update
        if isinstance(update_coin, Coin) and update_coin.name in list_all_coins:
            # updates coins in balance
            if update_coin.coin_in_balance:
                coins_in_balance = coins_in_balance + 1
                coins_in_balance_list.append(update_coin.name)
            # assigns coin power
            try:
                # ensures coin have been trading for at least 3 days
                if len(update_coin.data["close"][:current_date]) > 2*24*30:
                    # calculates coin power
                    # this method use previous close * sum of volume last 24 hours
                    update_coin.power = update_coin.data.loc[:current_date, "close"].to_list()[-2] * \
                                        sum(update_coin.data.loc[:current_date, "volume"].to_list()[(-2 * 24) - 1:-2])
                    all_power.append(update_coin.power)
            except KeyError:
                update_coin.power = 0
                continue
    # buy and sell on only top 10% of coins
    all_power.sort(reverse=True)
    # limits the maximum coins to 20 coins
    if math.ceil(0.1*len(all_power)) > 19:
        limit = 19
    else:
        limit = math.ceil(0.1*len(all_power))
    power_limit = all_power[limit]
    # counts maximum number of coins for investment
    counter = len([power for power in all_power if power >= power_limit])
    for update_coin in gc.get_objects():  # used to determine the coin required for update
        if isinstance(update_coin, Coin) and update_coin.name in list_all_coins:
            update_coin.USDT_Balance = 0
            sell = False
            buy = False
            # tracks only coins in balance or exceeding power limit
            if update_coin.power >= power_limit or update_coin.coin_in_balance:
                # allocates USDT Balance for each coin if not in balance
                if not update_coin.coin_in_balance and (counter - coins_in_balance) > 0:
                    update_coin.USDT_Balance = current_USDT_balance / (counter - coins_in_balance)
                else:
                    update_coin.USDT_Balance = 0
                # finds buy and sell signals
                current_MACD_line_value = update_coin.data.loc[:current_date, "MACD_line"].to_list()[-1]
                previous_MACD_line_value = update_coin.data.loc[:current_date, "MACD_line"].to_list()[-2]
                current_MACD_signal_value = update_coin.data.loc[:current_date, "MACD_signal"].to_list()[-1]
                previous_MACD_signal_value = update_coin.data.loc[:current_date, "MACD_signal"].to_list()[-2]
                if current_MACD_line_value >= current_MACD_signal_value \
                        and previous_MACD_line_value < previous_MACD_signal_value:
                    buy = True
                    sell = False
                if current_MACD_line_value < current_MACD_signal_value:
                    sell = True
                    buy = False
                # executes buy and sell
                if buy and update_coin.USDT_Balance > 0 and not update_coin.coin_in_balance:
                    update_coin.coin_in_balance = True
                    # 0.1% for Binance fees
                    update_coin.coin_balance = update_coin.USDT_Balance * 0.999 / update_coin.data["close"][current_date]
                    print("Buy", current_date, update_coin.name, str(round(update_coin.USDT_Balance, 2)))
                    update_coin.last_buy_price = update_coin.data["close"][current_date]
                    current_USDT_balance = current_USDT_balance - update_coin.USDT_Balance
                    update_coin.USDT_Balance = 0
                    coins_in_balance = coins_in_balance + 1
                    update_coin.buy_date = current_date
                    coins_in_balance_list.append(update_coin.name)
                elif sell and update_coin.coin_in_balance:
                    update_coin.coin_in_balance = False
                    # 0.1% for Binance fees
                    update_coin.USDT_Balance = update_coin.coin_balance * update_coin.data["close"][current_date] * 0.999
                    print("Sell", current_date, update_coin.name, str(round(update_coin.USDT_Balance, 2)))
                    update_coin.transactions = update_coin.transactions + 1
                    current_USDT_balance = current_USDT_balance + update_coin.USDT_Balance
                    coins_in_balance = coins_in_balance - 1
                    holding_time = (current_date - update_coin.buy_date).seconds
                    holding_time_list.append(holding_time)
                    if update_coin.data["close"][current_date] >= update_coin.last_buy_price:
                        pos_transactions_net_change.append((update_coin.data["close"][current_date] - update_coin.last_buy_price) / update_coin.last_buy_price)
                        pos_transactions_net.append(update_coin.coin_balance * (update_coin.data["close"][current_date] - update_coin.last_buy_price))
                    else:
                        neg_transactions_net_change.append((update_coin.last_buy_price - update_coin.data["close"][
                            current_date]) / update_coin.last_buy_price)
                        neg_transactions_net.append(update_coin.coin_balance * (
                                update_coin.last_buy_price - update_coin.data["close"][current_date]))
                    update_coin.last_buy_price = 0.0
                    update_coin.coin_balance = 0
            if update_coin.coin_in_balance:
                try:
                    my_new_portfolio = my_new_portfolio + update_coin.coin_balance * update_coin.data.loc[current_date, "close"]
                except KeyError:
                    my_new_portfolio = my_new_portfolio + update_coin.coin_balance * update_coin.last_buy_price
            else:
                my_new_portfolio = my_new_portfolio
    my_new_portfolio = my_new_portfolio + current_USDT_balance
    # checks start of day
    my_portfolio_profile_dates.append(current_date)
    my_portfolio_profile.append(my_new_portfolio)
    my_portfolio_profile_change.append(my_new_portfolio / investment_USDT)
    current_date = current_date + dt.timedelta(minutes=30)
    if current_date.hour == 0 and current_date.minute == 0:
        print(current_date, "Current Portfolio", str(round(my_new_portfolio, 2)), "Available USDT",
              str(round(current_USDT_balance, 2)), "Coins in balance", coins_in_balance)
    if current_date == end_date:
        print("Coins in Balance:", coins_in_balance_list)
        print("Coins in Balance:", len(coins_in_balance_list))

# calculates Average profit per trade (APPT)
total_trades = len(pos_transactions_net_change) + len(neg_transactions_net_change)
# calculates probability of win and loss
PW = len(pos_transactions_net_change) / total_trades  # Probability of Winning trade
PL = len(neg_transactions_net_change) / total_trades  # Probability of Losing trade
AW = np.average(pos_transactions_net_change)  # Average Win per trade
AL = np.average(neg_transactions_net_change)  # average Loss per trade
APPT = AW * PW - AL * PL  # Average profit per trade
print("#############################################")
print("Simulation from", start_date, "to", end_date)
print("Total number of trades:", total_trades)
print("Probability of Winning trades:", str(round(PW, 3)))
print("Average Win per winning trade:", str(round(AW, 3)))
print("Average Loss per losing trade:", str(round(AL, 3)))
print("Average profit per trade (APPT):", str(round(APPT, 3)))
print("Profit factor:", str(round((AW*PW)/(AL*PW), 3)))
print("Profit factor:", str(round(sum(pos_transactions_net)/(sum(neg_transactions_net)), 3)))
print("Average holding time:", str(round(np.average(holding_time_list)/60/60, 2)))

# used for comparison with BTC change
BTC_data = pd.read_csv(str("History CSV Files//" + "BTCUSDT" + "_" + interval + ".csv"), header=None)
BTC_data.columns = ["UNIX_Datetime", "open", "high", "low", "close", "volume"]
BTC_data.index = [dt.datetime.fromtimestamp(x / 1000.0) for x in BTC_data["UNIX_Datetime"]]
BTC_data = BTC_data[start_date:end_date]
BTC_change = [1]
for price in BTC_data["close"][1:]:
    BTC_change.append(price/BTC_data["close"][0])

# plot Asset Net Worth
plt.plot(my_portfolio_profile_dates, my_portfolio_profile)
plt.suptitle("Assets Net Worth, V4.10")
plt.grid(True)
plt.show()
# plot PNL vs BTC
plt.plot(my_portfolio_profile_dates, BTC_change, label="BTC Cumulative PNL %", color="black")
plt.plot(my_portfolio_profile_dates, my_portfolio_profile_change, label="Portfolio Cumulative PNL %", color="green")
plt.suptitle("Cumulative PNL %, V4.10")
legend = plt.legend()
plt.grid(True)
plt.show()
