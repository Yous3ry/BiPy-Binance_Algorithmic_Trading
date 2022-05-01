import datetime as dt  # used for datetime
import json  # used to get received data
import requests  # used for API history loading
import pandas as pd  # used for data manipulation
from os import path  # used to read files
import time


def download_coin_files(req_start_date, req_end_date, list_of_coins, interval):
    # gets coin data after end date and saves as CSV files
    count = 1
    for download_coin in list_of_coins:  # used to determine the coin required for action
        coin_name = download_coin.upper()
        print("#", count, "Downloading", coin_name)
        coin_path = str("History CSV Files//" + download_coin + "_" + interval + ".csv")
        print(coin_path)
        try:  # used to avoid errors when there is a coin with too short history
            if path.exists(coin_path):
                loaded_data = pd.read_csv(coin_path, header=None)
                loaded_data = loaded_data.iloc[:-5]
                print("Coin last DB date", dt.datetime.fromtimestamp(loaded_data[0][len(loaded_data[0]) - 1] / 1000))
                updated_start_date = dt.datetime.fromtimestamp(loaded_data[0][len(loaded_data[0]) - 1] / 1000) \
                                     + dt.timedelta(minutes=1)
                final_data = loaded_data
            else:
                print("New Coin")
                updated_start_date = req_start_date
                final_data = pd.DataFrame()
        except IndexError:
            print("New Coin")
            updated_start_date = req_start_date
            final_data = pd.DataFrame()
        # starts simulation at the end of fake data loaded
        step_start_date = updated_start_date
        # end data to ask the server
        if interval == "1m":
            step_end_date = step_start_date + dt.timedelta(minutes=500)
        elif interval == "5m":
            step_end_date = step_start_date + dt.timedelta(minutes=1000)
        elif interval == "15m":
            step_end_date = step_start_date + dt.timedelta(minutes=1500)
        elif interval == "30m":
            step_end_date = step_start_date + dt.timedelta(minutes=3000)
        elif interval == "1h":
            step_end_date = step_start_date + dt.timedelta(hours=500)
        elif interval == "1d":
            step_end_date = step_start_date + dt.timedelta(days=500)
        else:
            print("Unrecognized time interval for {}".format(coin_name))
            step_end_date = 0
            exit()
        # checks and correct the end date time
        if step_end_date > end_date:
            step_end_date = end_date
        # gets data from server ands to CSV file every 1 day until 2021
        while step_start_date < req_end_date:
            # API url
            url = "https://api.binance.com/api/v3/klines"
            # converts start and end date to UNIX format for API
            start_time = str(int(step_start_date.timestamp() * 1000))
            end_time = str(int(step_end_date.timestamp() * 1000))
            # specify parameters to load
            req_params = {"symbol": coin_name, 'interval': interval,
                          'startTime': start_time, 'endTime': end_time}
            # Downloading data
            try:
                data = pd.DataFrame(json.loads(requests.get(url, params=req_params).text))
            except TimeoutError:
                time.sleep(10)  # wait for 10 seconds
                data = pd.DataFrame(json.loads(requests.get(url, params=req_params).text))
            # gets only important data
            data = data.iloc[:, 0:6]
            # writes data to CSV
            # checks if results are empty
            if len(data.index) > 0:
                final_data = pd.concat([final_data, data])  # appends to final data
            # incremental steps
            if interval == "1m":
                step_start_date = step_end_date + dt.timedelta(minutes=1)
                step_end_date = step_end_date + dt.timedelta(minutes=500)
            elif interval == "15m":
                step_start_date = step_end_date + dt.timedelta(minutes=1)
                step_end_date = step_end_date + dt.timedelta(minutes=1500)
            elif interval == "30m":
                step_start_date = step_end_date + dt.timedelta(minutes=1)
                step_end_date = step_end_date + dt.timedelta(minutes=3000)
            elif interval == "1h":
                step_start_date = step_end_date + dt.timedelta(hours=1)
                step_end_date = step_end_date + dt.timedelta(hours=500)
            elif interval == "1d":
                step_start_date = step_end_date + dt.timedelta(days=1)
                step_end_date = step_end_date + dt.timedelta(days=500)
        # print final data to file
        final_data.drop_duplicates(subset=[0], keep="last")
        final_data.drop_duplicates(subset=[0], keep="last")
        final_data = final_data.iloc[:-1]
        final_data.to_csv(str("History CSV Files//" + coin_name + "_" + interval + ".csv"),
                          index=False, header=False, mode="w")
        # resets start datetime
        updated_start_date = req_start_date
        count = count + 1
    print("Fake files created")


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

# used to avoid some downloading issues
list_all_coins.sort()

# download history files for analysis
start_date = dt.datetime(2017, 1, 1)  # older than the oldest data on binance
end_date = dt.datetime.now()
# download files
download_coin_files(start_date, end_date, list_all_coins, "30m")

# Excel UNIX Function for QC =(A1/86400/1000)+DATE(1970,1,1)
