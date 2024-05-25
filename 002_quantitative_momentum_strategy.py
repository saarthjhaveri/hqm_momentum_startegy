import numpy as np
import pandas as pd
import math
import requests
from scipy import stats
import datetime
import yfinance as yf
import xlsxwriter
from statistics import mean

from scipy.stats import percentileofscore as score

stocks = pd.read_csv('./../sp_500_stocks.csv')

print(stocks)


def symbol_exists(symbol):
    try:
        # Attempt to create a Ticker object
        yf.Ticker(symbol)
        return True
    except ValueError:
        print("error is ", ValueError)
        return False


def get_stock_return(symbol, start_date, end_date):
    if not symbol_exists(symbol):
        print(f"Symbol {symbol} doesnt exist")
        return 0, 0
    # Fetch historical data for the given stock symbol

    stock_data = yf.download(symbol, start=start_date, end=end_date)
    # If no data found for a particular stock
    if (len(stock_data) == 0):
        return 0, 0
    # Closing price of the stock today
    price = stock_data.iloc[-1]['Close']

    # Calculate the daily returns
    stock_data['Daily_Return'] = stock_data['Adj Close'].pct_change()
    cumulative_return = (stock_data['Daily_Return'] + 1).prod() - 1

    return cumulative_return, price

#high quality momentum strategy
hqm_cols = [
    'ticker',
    'price',
    'sharesToBuy',
    'one_year_return_price',
    'one_year_return_percentile',
    'six_month_return_price',
    'six_month_return_percentile',
    'three_month_return_price',
    'three_month_return_percentile',
    'one_month_return_price',
    'one_month_return_percentile'
]

hqm_df = pd.DataFrame(columns=hqm_cols)

for stock in stocks['Ticker'][:100]:
    symbol = stock  # Example stock symbol (Apple Inc.)
    today = datetime.date.today()
    end_date = today
    start_date = today - datetime.timedelta(days=365)
    return_one_year, price = get_stock_return(symbol, start_date, end_date)
    end_date = today - datetime.timedelta(days=180)
    return_six_month, price = get_stock_return(symbol, start_date, end_date)
    end_date = today - datetime.timedelta(days=90)
    return_three_month, price = get_stock_return(symbol, start_date, end_date)
    end_date = today - datetime.timedelta(days=30)
    return_one_month, price = get_stock_return(symbol, start_date, end_date)

    new_row = {'price': price, 'ticker': symbol, 'sharesToBuy': np.nan, 'one_year_return_price': return_one_year,
               'one_year_return_percentile': np.nan, 'six_month_return_price': return_six_month,
               'six_month_return_percentile': np.nan, 'three_month_return_price': return_three_month,
               'three_month_return_percentile': np.nan, 'one_month_return_price': return_one_month,
               'one_month_return_percentile': np.nan, 'hqm_score': np.nan}

    hqm_df = hqm_df._append(new_row, ignore_index=True)

time_period_cols = [
    'one_year',
    'six_month',
    'three_month',
    'one_month'
]

for row in hqm_df.index:
    for time_period in time_period_cols:
        price_col = f'{time_period}_return_price'
        percentile_col = f'{time_period}_return_percentile'
        hqm_df.loc[row, percentile_col]= score(hqm_df[price_col], hqm_df.loc[row,price_col])


# calculate hqm (high quality momentum score) using mean, it is basically the mean of all the 4 percentiles for a
# particular stock
for row in hqm_df.index:
    momentum_percentiles=[]
    for time_period in time_period_cols:
        momentum_percentiles.append(hqm_df.loc[row,f"{time_period}_return_percentile"])

    hqm_df.loc[row,'hqm_score']= mean(momentum_percentiles)


#sort the df according to the hqm_score and then pick the 50 top most stocks with highest momentum

hqm_df.sort_values('hqm_score', inplace=True, ascending=False)
hqm_df = hqm_df[:50]
hqm_df.reset_index(inplace=True)
hqm_df = hqm_df.drop('index', axis='columns')





#following code is for the user interaction which suggests how many shares to buy from the top 50 hqm_score of the equal weighted s&p 500 index fund
#insert the size of portfolio and it will return the number of shares and which shares to buy
def get_portfolio_size():
    global portfolio_size
    portfolio_size = input("Eneter the size of portoflio")

    try:
        float(portfolio_size)
    except ValueError:
        print("This is not a correct format please enter float value ")
        portfolio_size = input("Enter the size of portflio")

get_portfolio_size()
print("pf size", portfolio_size)

position_size = float(portfolio_size) / len(hqm_df.index)

print("position size is ", position_size)

for i in range(0, len(hqm_df)):
    hqm_df.loc[i, 'sharesToBuy'] = math.floor(position_size / hqm_df.loc[i, 'price'])



writer =pd.ExcelWriter('momentum_startegy.xlsx', engine='xlsxwriter')

hqm_df.to_excel(writer,sheet_name='Momentum_startegy', index= False)

writer.close()
