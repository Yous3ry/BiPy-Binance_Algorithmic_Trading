# BiPy-Binance Python algorithmic trading
Cryptocurrency Algorithmic trading via Binance platform with live updates using Telegram bot.

### Disclaimer:
The client’s actual trading logic has been changed due to confidentiality. The trading logic in the code is intended for illustration only.
Please UPDATE all trading logic parameters as you see fit.


## Table of Contents
1. [Features](#Features)
2. [User data](#User-data)
3. [Dependencies](#Dependencies)


## Features
1. Download all/selected historical cryptocurrency data \[open, high, low, close] and save to CSV (using user-defined time interval). ([Download_History.py](https://github.com/Yous3ry/BiPy-Binance_Algorithmic_Trading/blob/main/Download_History.py))
2. Back testing different trading strategies \[MA, EMA, MACD, Bollinger bands, RSI, etc.] using Python Technical Analysis Library (ta) to evaluate their efficiency. ([Coin_Back_testing.py](https://github.com/Yous3ry/BiPy-Binance_Algorithmic_Trading/blob/main/Coin_Back_testing.py))
3. Back testing trading multiple coins simultaneously where coin selection is based on user-defined logic. ([Back_testing_with_Coin_Selection.py](https://github.com/Yous3ry/BiPy-Binance_Algorithmic_Trading/blob/main/Back_testing_with_Coin_Selection.py))
4. Forward testing (Live testing) the compiled script with live updates sent to users with a Telegram bot. Actions and results are stored in CSV files for evaluation. ([Forward_testing_Bot.py](https://github.com/Yous3ry/BiPy-Binance_Algorithmic_Trading/blob/main/Forward_testing_Bot.py)). Also Available without the bot feature. ([Forward_testing.py](https://github.com/Yous3ry/BiPy-Binance_Algorithmic_Trading/blob/main/Forward_testing.py))
5. Live project that conducts actual buy and sell action on Binance Platform with live updates sent to users with a Telegram bot. ([Live_Project_bot.py](https://github.com/Yous3ry/BiPy-Binance_Algorithmic_Trading/blob/main/Live_Project_bot.py))


## User data
Remember to change:
1. Binance API codes: API_Key and API_Secret
2. Telegram Bot codes: bot_token, phone, api_id, api_hash

## Dependencies
python-binance, ta, telethon
