from ta import trend as ta_trend  # used to calculate the different trend indicators
from ta import momentum as ta_momentum  # used to calculate the different momentum indicators
from ta import volatility as ta_volt  # used to calculate the different volatility indicators
import pandas as pd  # used for data manipulation
import datetime as dt  # used for datetime
import matplotlib.pyplot as plt  # used for plotting
import json  # used to get received data
import requests  # used for API history loading
import numpy as np


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
# Activate to test certain coins
list_all_coins = ["BTCUSDT", "BNBUSDT", "ETHUSDT"]

# define trading interval
interval = "30m"


# Initialize totals
initial_investment = 100
all_coins_USDT_Balance = 0.0
holding_USDT = 0.0
num_coins = 0
wining_pairs = 0
losing_pairs = 0
# read history files
for fake_coin in list_all_coins:  # used to determine the coin required for action
    # load first day as history into coin
    try:
        data = pd.read_csv(str("History CSV Files//" + fake_coin + "_" + interval + ".csv"), header=None)
    except FileNotFoundError:
        continue
    data.columns = ["UNIX_Datetime", "open", "high", "low", "close", "volume"]
    data["date"] = [dt.datetime.fromtimestamp(x / 1000.0) for x in data["UNIX_Datetime"]]
    data.index = [dt.datetime.fromtimestamp(x / 1000.0) for x in data["UNIX_Datetime"]]
    data["change"] = abs(data["close"] - data["open"])
    # Calculates moving average indicators
    data['MA50'] = data["close"].rolling(window=50).mean().astype("float")
    data['MA100'] = data["close"].rolling(window=100).mean().astype("float")
    data['MA200'] = data["close"].rolling(window=200).mean().astype("float")
    # Calculates Exponential moving average indicators
    data["EMA50"] = ta_trend.ema_indicator(pd.Series(data["close"]), 50).astype("float")
    data["EMA100"] = ta_trend.ema_indicator(pd.Series(data["close"]), 100).astype("float")
    data["EMA200"] = ta_trend.ema_indicator(pd.Series(data["close"]), 200).astype("float")
    # Calculates Moving Average Convergence / Divergence (MACD) indicator default 26, 12, 9
    data["MACD_line"] = ta_trend.macd(pd.Series(data["close"]), 26, 12).astype("float")
    data["MACD_signal"] = ta_trend.macd_signal(pd.Series(data["close"]), 26, 12, 9).astype("float")
    # Calculates the Relative Strength Index (RSI) overbought >= 70 and oversold <= 30, default 14
    data["RSI"] = ta_momentum.rsi(pd.Series(data["close"]), 14).astype("float")
    # calculates bollinger bands
    data["boll_h_band"] = ta_volt.bollinger_hband(data['close'], 21, 2)  # returns high band series
    data["boll_avg_band"] = ta_volt.bollinger_mavg(data['close'], 21, 2)  # returns avg band series
    data["boll_l_band"] = ta_volt.bollinger_lband(data['close'], 21, 2)  # returns low band series
    # calculates support and resistance
    data["ADX"] = ta_trend.adx(data['high'], data['low'], data['close'], 14).astype("float")
    data["ADX_pos"] = ta_trend.adx_pos(data['high'], data['low'], data['close'], 14).astype("float")
    data["ADX_neg"] = ta_trend.adx_neg(data['high'], data['low'], data['close'], 14).astype("float")
    # end of calculations
    print(fake_coin.upper(), "history loaded and Calculations done")
    # initializes fake balance
    available_USDT_balance = initial_investment
    # initializes fake coin balance
    coin_in_balance = False
    coin_balance = 0.0
    # defines operations net income
    net_income = []
    net_income_dates = []
    total_position = []
    buy_dates = []
    buy_values = []
    sell_dates = []
    sell_values = []
    last_USDT_balance = 0.0
    pos_transactions_net = []
    neg_transactions_net = []
    # fake reads history files as live data
    print("Simulating History...")
    start_idx = 200  # Ensures enough history for indicators to work
    # main loop
    if len(data["close"]) > start_idx:
        num_coins = num_coins + 1
        # calculates holding gain
        equivalent_coins = available_USDT_balance / data["close"][start_idx]
        holding_USDT = holding_USDT + equivalent_coins * data["close"][-1]

        for i in range(0, len(data["close"])):  # start at first minute after history
            # Decide actions based on indicators
            buy = False
            sell = False
            # Buying Condition
            if data["MACD_line"][i] > data["MACD_signal"][i]:
                buy = True
                sell = False
            if data["MACD_line"][i] < data["MACD_signal"][i]:
                sell = True
                buy = False
            # sell at last point of data
            if i == len(data["close"]) - 1:
                sell = True
            # buy and sell actions
            if buy and (not coin_in_balance):
                if available_USDT_balance > 0:
                    buy_price = data["close"][i]
                    # 0.1% for Binance fees
                    coin_balance = available_USDT_balance * 0.999 / data["close"][i]
                    coin_in_balance = True
                    last_USDT_balance = available_USDT_balance
                    available_USDT_balance = 0.0
                    sell_price = 0
                    buy_dates.append(data.index[i])
                    buy_values.append(data["close"][i])
            elif sell and coin_in_balance:
                if coin_balance > 0:
                    sell_price = data["close"][i]
                    if sell_price >= buy_price:
                        pos_transactions_net.append(coin_balance * (sell_price - buy_price))
                    else:
                        neg_transactions_net.append(coin_balance * (buy_price - sell_price))
                    buy_price = 0
                    # 0.1% for Binance fees
                    available_USDT_balance = available_USDT_balance + coin_balance * data["close"][i] * 0.999
                    coin_in_balance = False
                    # Calculate results after selling
                    net_income.append(available_USDT_balance - last_USDT_balance)
                    net_income_dates.append(data.index[i])
                    total_position.append(available_USDT_balance)
                    sell_dates.append(data.index[i])
                    sell_values.append(data["close"][i])
        # calculating the transactions statistics
        positive_transactions = sum(np.array(net_income) >= 0)
        negative_transactions = sum(np.array(net_income) < 0)
        total_transactions = len(net_income)
        # prints results
        try:
            print(fake_coin.upper(), "start price is:", data["close"][start_idx], "and the end price is:",
                  data["close"][-1])
            print(fake_coin.upper(), "Price percentage change is:",
                  str(round((data["close"][-1] / data["close"][0]) * 100, 2)))
            print(fake_coin.upper(), "start investment is:", 100, "and the end investment is:", total_position[-1])
            print(fake_coin.upper(), "Investment percentage change is:",
                  str(round((total_position[-1] / 100) * 100, 2)))
            print("number of transactions:", total_transactions)
            print("number of +ve transactions:", positive_transactions,
                  str(round(positive_transactions / total_transactions * 100, 2)))
            print("number of -ve transactions:", negative_transactions,
                  str(round(negative_transactions / total_transactions * 100, 2)))
            print("Profit Factor:", str(round(sum(pos_transactions_net) / sum(neg_transactions_net), 3)))
        except IndexError:
            continue
        print(fake_coin.upper(), "Simulation done")
        # counts coins results
        if initial_investment * 0.9 > total_position[-1]:
            losing_pairs = losing_pairs + 1
        else:
            wining_pairs = wining_pairs + 1
        # plotting Results
        fig, (ax1, ax2, ax3) = plt.subplots(3, sharex=True)
        ax1.plot(net_income_dates, total_position)
        fig.suptitle(str(fake_coin.upper() + " Simulation results"))
        ax1.grid(True)
        ax2.plot(data.index, data["close"], label="Close Values", color="black")
        ax2.plot(data.index, data["EMA50"], label="EMA50", color="blue")
        ax2.plot(data.index, data["EMA100"], label="EMA100", color="orange")
        ax2.plot(data.index, data["EMA200"], label="EMA200", color="green")
        ax2.plot(buy_dates, buy_values, "^", color="green")
        ax2.plot(sell_dates, sell_values, "v", color="red")
        ax2.grid(True)
        legend = ax2.legend()
        ax3.plot(data.index, data["MACD_line"], color="black")
        ax3.plot(data.index, data["MACD_signal"], color="red")
        ax3.grid(True)
        plt.show()
        # summary of holding
        try:
            all_coins_USDT_Balance = all_coins_USDT_Balance + total_position[-1]
        except IndexError:
            continue
print("initial investment is:", num_coins * initial_investment, "USDT")
print("all coins USDT Balance:", all_coins_USDT_Balance)
print("all coins holding USDT Balance:", holding_USDT)
print("losing coins count (<90% Capital)", losing_pairs)
print("wining coins count", wining_pairs)
print("All Done")
