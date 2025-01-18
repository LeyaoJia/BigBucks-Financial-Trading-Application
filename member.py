from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request, jsonify
from flask import url_for
import requests
import json

import numpy as np
import pandas as pd
from Bigbucks.historical import collect_stock_data
from Bigbucks.historical import get_10year_yield


from Bigbucks.config import api_key
# from config import token


from Bigbucks.auth import login_required
from Bigbucks.db import get_db


bp = Blueprint("member", __name__)



# =============INDEX STARTS===================
def get_news():
    url = 'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&apikey='+api_key
    r = requests.get(url)
    data = r.json()
    return data

@bp.route("/", methods=("POST","GET"))
@login_required
def index():
    db = get_db()
    news = get_news()
    data = db.execute(
        "SELECT *"
        " FROM stock s JOIN user u ON u.id=s.user_id"
    ).fetchall()
    return render_template("member/index.html", data = data, news = news)

# =============INDEX ENDS===================




# =============TRADE STARTS===================
def get_cash_balance():
    """Get the current cash balance for the current user.
    Cash is a sqlite3.Row object, use cash[0] to get the integer.
    """
    cash = (
        get_db()
        .execute(
            "SELECT cash"
            " FROM user"
            " WHERE id = ?",
            (g.user["id"],)
        )
        .fetchone()
    )
    return cash[0]

def get_name(symbol):
    name = (
        get_db()
        .execute(
            "SELECT name"
            " FROM stock s"
            " WHERE s.symbol = ?",
            (symbol,),
        )
        .fetchone()
    )
    return name[0]
    
def get_share_balance(symbol):
    """Get the # of shares held for a ticker specified in a trade for the current user."""
    shares_bought = (
        get_db()
        .execute(
            "SELECT SUM(s.share)"
            " FROM stock s JOIN user u ON u.id=s.user_id"
            " WHERE s.act = ? and s.symbol = ? and u.id = ?",
            ("buy",symbol, g.user["id"],),
        )
        .fetchone()
    )

    shares_sold  = (
        get_db()
        .execute(
            "SELECT SUM(s.share)"
            " FROM stock s JOIN user u ON u.id=s.user_id"
            " WHERE s.act = ? and s.symbol = ? and u.id = ?",
            ("sell",symbol, g.user["id"],),
        )
        .fetchone()
    )   

    if shares_bought[0] == None:
        shares_buy = 0
    else:
        shares_buy = shares_bought[0]
    
    if shares_sold[0] == None:
        shares_sell = 0
    else:
        shares_sell = shares_sold[0]
    
    holding_shares = shares_buy - shares_sell
    return holding_shares


# def get_actdate_price(symbol, date):
#     url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=" + symbol+ "&outputsize=full&apikey=" + api_key
#     r = requests.get(url)
#     data = r.json()
    
#     # check if the input symbol doesn't exist
#     # if data['Error Message']!= None:
#     #     flash("1. Invalid API call: Wrong symbol!")
#     # else:
#     # 需要添加判断输入的日期是否是business day
#         # try:
#     actdate_price = data["Time Series (Daily)"][date]["5. adjusted close"]
#     return float(actdate_price)
#         # except:
#         #     error = "Invald date entered! Please use format YYYY-MM-DD!"
#         #     flash(error)

    
def get_current_price(symbol):
    url = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol="+symbol+"&interval=5min&apikey="+api_key
    # url = "https://api.iex.cloud/v1/data/CORE/QUOTE/"+symbol+"?token="+token

    r = requests.get(url)
    data = json.loads(r.text) 

    latest_timestamp = max(data['Time Series (5min)']) if 'Time Series (5min)' in data else None
    if latest_timestamp:
        current_price = data['Time Series (5min)'][latest_timestamp]['4. close']
        current_price = float(current_price)
    else:
        current_price = None  # 如果没有数据，返回None或适当的错误处理
    
    return current_price


# define a new function to get the company's name corresponding to a stock
def get_stock_name(symbol):
    url = "https://www.alphavantage.co/query?function=OVERVIEW&symbol="+symbol+"&interval=5min&apikey="+api_key
    response = requests.get(url)
    data = response.json()
    return data["Name"]


@bp.route("/trade", methods=("GET", "POST"))
@login_required
def trade():
    """Create a new trade for the current user."""
    if request.method == "POST":
        symbol = request.form["symbol"]
        symbol = symbol.upper()
        # date = request.form["date"]
        act = request.form["act"]
        shares = request.form["shares"]
        
        error = None

        if not symbol:
            error = "Stock symbol is required for the trade."
        if not act:
            error = "Action is required for the trade."
        if not shares:
            error = "Number of shares is required for the trade."

        try:
            shares = int(shares)
        except:
            error = "Number of shares should be an integer."
            flash(error)
            return render_template("member/trade.html")

        if shares <= 0:
            error = "Number of shares should be positive."
            flash(error)
            return render_template("member/trade.html")

        if shares%100 != 0:
            error = "Number of shares should be a multiple of 100."
            flash(error)
            return render_template("member/trade.html")

        try:
            cprice = get_current_price(symbol)
        except:
            error = "Invalid symbol or api_key!"
            flash(error)
            return render_template("member/trade.html")
        
        # try:
        #     actdate_price = get_actdate_price(symbol, date)
        # except:
        #     error = "Invalid trading date or api_key!"
        #     flash(error)
        #     return render_template("member/trade.html")
        
        try:
            name = get_stock_name(symbol)
        except:
            error = "Invalid symbol or api_key!"
            flash(error)
            return render_template("member/trade.html")
        

        cash = get_cash_balance()
       
        # get the current number of shares held for a specified stock ticker
        holding_shares = get_share_balance(symbol)

        #error = None
        

        if act=="buy":
            buy = True
            if cash >= shares * cprice:
                cash -= shares * cprice
                collect_stock_data(symbol)
                # stock = BigBucks.classes.Stock(symbol)
                collect_stock_data("SPY")
            else:
                error = "Not enough cash to excute the trade!"

        if act=="sell":
            buy=False
            try:
                if holding_shares >= shares:
                    cash += shares * cprice
                    holding_shares -= shares
                else:
                    error = "Not enough shares held to be sold!"
            except:
                error = "You don't hold any " + symbol +" stock!"

        if act!="buy" and act!="sell":
            error = "Action must be either \"buy\" or \"sell\"."
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO stock (symbol, name, buy, act, share, actprice, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (symbol, name, buy, act, shares, cprice, g.user["id"]),
            )
            db.execute(
                "UPDATE user SET cash = ? where id = ?",
                (cash,g.user["id"]),
            )
            db.commit()
            flash('Success!')
            return redirect(url_for("member.trade"))
            #return render_template("member/profile.html")

    db = get_db()
    trades = db.execute(
        "SELECT *"
        " FROM stock s JOIN user u ON u.id = s.user_id"
        " WHERE s.user_id = ?"
        " ORDER BY added DESC",
        (g.user["id"],)
    ).fetchall()

    return render_template("member/trade.html", trades = trades)

# =============TRADE ENDS===================




# =============HOLDING STARTS===================

@bp.route("/holding", methods=("GET", "POST"))
@login_required
def holding():
    db = get_db()

    cash = get_cash_balance()

    symbols = db.execute(
        "SELECT DISTINCT symbol"
        " FROM stock s JOIN user u ON u.id = s.user_id"
        " WHERE s.user_id = ?"
        " ORDER BY added DESC",
        (g.user["id"],)
    ).fetchall()

    # store existing symbols in the database to a list
    existing_symbols = []
    for i in range(len(symbols)):
        existing_symbols.append(symbols[i][0])
    
    # store current prices in a dict
    # store names in a dict
    # compute share balance of each stock and store them in a dictionary
    share_balance = {}
    current_prices = {}
    names = {}
    for i in existing_symbols:
        current_prices[i] = get_current_price(i)
        names[i] = get_name(i)
        shares = get_share_balance(i)
        if shares == 0:
            continue
        else:
            share_balance[i] = shares
    
    #get_rv(): answer = {'rv': rv, 'pf': pf, 'cov': annual_cov} / pf = [sharpe_ratio, port_return, port_vol]
    pf = get_rv()['pf']

    return render_template("member/holding/holding.html", names=names, current_prices=current_prices, cash=cash, share_balance=share_balance, pf = pf)


@bp.route("/<symbol>/graph", methods=("GET", "POST"))
@login_required
def graph(symbol):
    db = get_db()
    
    data = db.execute(
        "SELECT *"
        " FROM stock s JOIN HistData h ON s.symbol = h.symbol"
        " WHERE s.user_id = ?"
        " ORDER BY added DESC",
        (g.user["id"],)
    ).fetchall()

    tickers = db.execute(
        "SELECT distinct symbol"
        " FROM stock s "
        " WHERE s.user_id = ?"
        " ORDER BY added DESC",
        (g.user["id"],)
    ).fetchall()

    new_tickers = []
    for ticker in tickers:
        if get_share_balance(ticker['symbol']) > 0:
            new_tickers.append(ticker)
    tickers = new_tickers


    return render_template("member/holding/graph.html", symbol = symbol, data = data, tickers=tickers)


# ===Selected symbol data fetched from db===
def get_selected_symbol_data(selected_symbol):
    db = get_db()
    # Retrieve data from the database based on the selected symbol
    data = db.execute(
        "SELECT symbol, date, close"
        " FROM HistData"
        " WHERE symbol=?",
        (selected_symbol,)
    ).fetchall()
    return data

# =============First Four Graphs Starts==========

# create an endpoint for js to fetch data
@bp.route('/get_hitorical_close_data', methods=['POST'])
def get_hitorical_close_data():
    db = get_db()
    selected_symbol = request.json["symbol"]

    # Retrieve data from the database based on the selected symbol
    data = db.execute(
        "SELECT h.date, h.close"
        " FROM stock s JOIN HistData h ON s.symbol = h.symbol"
        " WHERE s.user_id = ? and s.symbol=?",
        (g.user["id"], selected_symbol)
    ).fetchall()

    # Convert the data to a list of dictionaries
    data_dict = []
    for row in data:
        data_dict.append({'Date': row['date'], 'Close': row['close']})

    return jsonify(data_dict)

@bp.route('/get_hitorical_return_data', methods=['POST'])
def get_hitorical_return_data():
    db = get_db()
    selected_symbol = request.json["symbol"]

    # Retrieve data from the database based on the selected symbol
    data = db.execute(
        "SELECT h.date, h.close"
        " FROM stock s JOIN HistData h ON s.symbol = h.symbol"
        " WHERE s.user_id = ? and s.symbol=?",
        (g.user["id"], selected_symbol)
    ).fetchall()

    # Convert the data to a list of dictionaries
    data_dict = []
    prev_close = None
    for row in data:
        if prev_close is not None:
            return_val = (row['close'] - prev_close) / prev_close
        else:
            return_val = None
        data_dict.append({'Date': row['date'], 'Return': return_val})
        prev_close = row['close']
    return jsonify(data_dict)

@bp.route('/get_return_comparison_data', methods=['POST'])
def get_return_comparison_data():
    db = get_db()
    selected_symbol = request.json["symbol"]

    # Retrieve data from the database based on the selected symbol
    data = db.execute(
        "SELECT h.date, h.close"
        " FROM stock s JOIN HistData h ON s.symbol = h.symbol"
        " WHERE s.user_id = ? and s.symbol=?",
        (g.user["id"], selected_symbol)
    ).fetchall()

    # Convert the data to a list of dictionaries
    data_dict = []
    prev_close = None # Initialize previous close price to None
    daily_return = None
    for row in data:
        if prev_close is not None:
            daily_return = (row['close'] - prev_close) / prev_close
            data_dict.append({'Return(-1)': prev_return, 'Return': daily_return})
        prev_close = row['close']
        prev_return = daily_return
    
    return jsonify(data_dict)

# ========First Four Graphs Ends========

# ===========Second Three Graphs Starts==================
@bp.route('/get_price_movement_data', methods=['POST'])
def get_price_movement_data():
    # db = get_db()
    selected_symbol = request.json["symbol"]

    # Retrieve data from the database based on the selected symbol
    target_stock_data = get_selected_symbol_data(selected_symbol)

    spy_data = get_selected_symbol_data("SPY")
    # spy_data = db.execute(
    #     "SELECT h.date, h.close"
    #     " FROM HistData h"
    #     " WHERE h.symbol=\"SPY\""
    #     ).fetchall()

    # Convert the data to a list of dictionaries
    target_dict = []
    spy_dict=[]

    for row in target_stock_data:
        target_dict.append({'date': row['date'], 'close': row['close']})
    for row in spy_data:
        spy_dict.append({'date': row['date'], 'close': row['close']})
    
    return jsonify({'target_data': target_dict, 'spy_data': spy_dict})

@bp.route('/get_two_returns_data', methods=['POST'])
def get_two_returns_data():
    # db = get_db()
    selected_symbol = request.json["symbol"]

    # Retrieve data from the database based on the selected symbol
    target_stock_data = get_selected_symbol_data(selected_symbol)

    spy_data = get_selected_symbol_data("SPY")
    
    target_dict = []
    spy_dict=[]

    prev_close = None
    for row in target_stock_data:
        if prev_close is not None:
            return_val = (row['close'] - prev_close) / prev_close
        else:
            return_val = None
        target_dict.append({'Date': row['date'], 'Return': return_val})
        prev_close = row['close']

    prev_close = None
    for row in spy_data:
        if prev_close is not None:
            return_val = (row['close'] - prev_close) / prev_close
        else:
            return_val = None
        spy_dict.append({'Date': row['date'], 'Return': return_val})
        prev_close = row['close']
    
    return jsonify({'target_data': target_dict, 'spy_data': spy_dict})

# ===========Second Three Graphs Ends=================


# =============Calculte stats Starts======================

def get_portfolio():
    # get user's holding stocks and weights
    db = get_db()
    trades = db.execute(
        "SELECT symbol"
        " FROM stock s JOIN user u ON u.id = s.user_id"
        " WHERE s.user_id = ?"
        " ORDER BY added DESC",
        (g.user["id"],)
    ).fetchall()
    
    stocks = list()
    for stock in trades:
       stocks.append(stock[0])

    shares = {}
    for symbol in stocks:
        shares[symbol] = get_share_balance(symbol)

    current_p = {}
    for symbol in stocks:
        current_p[symbol] = get_current_price(symbol)
    
    totalvalue = 0
    for symbol in shares.keys():
        totalvalue += shares[symbol]*current_p[symbol]
    

    portfolio = {}
    for symbol in stocks:
        if totalvalue != 0:
            if shares[symbol] != 0:
                portfolio[symbol] = round(current_p[symbol] * shares[symbol] / totalvalue,3)
    
    return portfolio


# Abstract get_returns() from portfolio_analyze() and add volativility for each stock to calculate EF
def get_rv():
    db = get_db()
    # update stored data in the database
    symbols_db = db.execute("""
            SELECT DISTINCT symbol 
            FROM HistData 
            ;
            """
        ).fetchall()
    # store existing symbols in the database to a list
    existing_symbols = []
    for i in range(len(symbols_db)):
        existing_symbols.append(symbols_db[i][0])
    # update the existing data
    for i in existing_symbols:
        collect_stock_data(i)

    portfolio = get_portfolio()

    # get the 10 year treasury daily updated yield
    treasury_yields = get_10year_yield()
    updated_yield = float(treasury_yields['data'][0]['value'])/100

    avg_returns = {}
    returns_df = pd.DataFrame()
    for symbol in portfolio.keys():
        prices_db = db.execute("""
            SELECT close 
            FROM HistData 
            WHERE symbol = ? 
            ORDER BY date;
            """, (symbol,)
        ).fetchall()

        # fetch price data from requested sql data and store them in a numpy array
        prices = []
        for i in range(len(prices_db)):
            prices.append(prices_db[i][0])
        prices = np.array(prices)

        # calculate return of each stock from those price data
        returns = []
        for i in range(len(prices)):
            if i == len(prices) - 1:
                break
            returns.append(np.log(prices[i+1] / prices[i]))
        returns = np.array(returns)
        
        returns1 = np.copy(returns)
        # check if returns have the same length as others
        if len(returns_df) != 0:
            if len(returns) < len(returns_df):
                returns0 = np.repeat(returns, (len(returns_df) // len(returns) + 1))
                returns1 = returns0[:len(returns_df)]
            else:
                returns1 = returns[:len(returns_df)]

        # combine these returns into a pandas dataframe
        returns_df[symbol] = returns1

        # calculate geometric mean return and annualize it
        avg_returns[symbol] = (np.product(1+returns) ** (1 / len(returns)) - 1) * 255
        
    # derive the covariance matrix from the dataframe of returns, and annualize these covariances
    daily_cov = returns_df.cov()
    annual_cov = daily_cov.multiply(255)

    # calculate portfolio's expected return
    port_return = 0
    for symbol in portfolio.keys():
        port_return += portfolio[symbol] * avg_returns[symbol]
    
    # calculate portfolio's volatility
    weights = []
    for i in portfolio.keys():
        weights.append(portfolio[i])
    port_vol = np.sqrt(np.dot(np.dot(np.array(weights), annual_cov), np.array(weights).T))
    
    # derive sharpe ratio of the portfolio with numbers above
    sharpe_ratio = (port_return - float(updated_yield)) / port_vol

    # construct a dataframe which contains avg_return and vol for each stock
    rv = pd.DataFrame()
    for i in portfolio.keys():
        a_vol = annual_cov[i][i] # calculate annualized vol for each stock
        df_new_row = pd.DataFrame({'returns': avg_returns[i], 'vol': a_vol}, index=[0])
        rv = pd.concat([rv, df_new_row])
        #rv = rv.append({'returns': avg_returns[i], 'vol': a_vol}, ignore_index=True)

    # construct pf for portfolio_analyze() function
    pf = [sharpe_ratio, port_return, port_vol]

    # combine the two
    answer = {'rv': rv, 'pf': pf, 'cov': annual_cov}

    return answer


# ===========EF Graph Starts==================
@bp.route('/get_ef_data', methods=['POST'])
def get_ef_data():
    answer = get_rv()
    rv = answer['rv']
    cov_matrix = answer['cov']
    returns = rv['returns']

    num_assets = len(returns)
    num_port = 5000

    port_returns = []
    port_volatilities = []
    for i in range(num_port):
        weights = np.random.random(num_assets)
        weights /= np.sum(weights)
        sim_returns = np.dot(weights, returns)
        vols = np.sqrt(np.dot(np.dot(weights, cov_matrix), weights.T))
        port_returns.append(sim_returns)
        port_volatilities.append(vols)

    # store it in dict
    result = {}
    result['returns'] = port_returns
    result['vol'] = port_volatilities
    result['current'] = []

    # store the current portfolio
    result['current'] = [round(answer['pf'][1],4), round(answer['pf'][2],4)]

    # print(result)
    return jsonify(result)

# ===========EF Graph Ends==================

# ===========Pie Chart Starts==================
@bp.route('/get_pie_data', methods=['POST'])
def get_pie_data():
    db = get_db()

    data = db.execute(
        "SELECT DISTINCT symbol"
        " FROM stock"
        " WHERE user_id = ?",
        (g.user["id"], )
    ).fetchall()

    # Convert the data to a list of dictionaries
    data_dict = []

    for row in data:
        shares = get_share_balance(row['symbol'])
        if shares == 0:
            continue
        else:
            value_percent = get_current_price(row['symbol'])*shares
            data_dict.append({'Symbol': row['symbol'], 'Value': value_percent})

    
    return jsonify(data_dict)

# ===========Pie Chart Ends==================

@bp.route("/ef", methods=("GET", "POST"))
def ef():
    db = get_db()

    tickers = db.execute(
        "SELECT distinct symbol"
        " FROM stock s "
        " WHERE s.user_id = ?"
        " ORDER BY added DESC",
        (g.user["id"],)
    ).fetchall()

    stock_num = len(tickers)

    pf = get_rv()['pf']

    return render_template("member/holding/ef.html", stock_num = stock_num, pf = pf)


# =============HOLDING ENDS===================



# =============ACCOUNT STARTS===================

@bp.route("/account", methods=("GET", "POST"))
@login_required
def account():
    db = get_db()

    user_info = db.execute(
        "SELECT *"
        " FROM user u "
        " WHERE u.id = ?",
        (g.user["id"],)
    ).fetchall()

    return render_template("member/account.html", user_info = user_info)

# ============ACCOUNT ENDS===================


# =============ACCOUNT STARTS===================

@bp.route("/delete", methods=("GET", "POST"))
@login_required
def delete():
    db = get_db()

    db.execute(
        "DELETE"
        " FROM user"
        " WHERE user.id = ?",
        (g.user["id"],)
    )

    db.execute(
        "DELETE"
        " FROM stock "
        " WHERE stock.user_id = ?",
        (g.user["id"],)
    )

    db.commit()

    flash('Account deleted! See you next time!')
    return render_template("auth/login.html")

# ============ACCOUNT ENDS===================