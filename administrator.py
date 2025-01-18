from flask import Blueprint
from flask import g
from flask import render_template
from flask import jsonify

from datetime import date, timedelta
from Bigbucks.member import get_current_price, get_name

import numpy as np
import pandas as pd
from Bigbucks.historical import collect_stock_data
from Bigbucks.historical import get_10year_yield
from scipy.optimize import minimize


from Bigbucks.auth import login_required
from Bigbucks.db import get_db


bp = Blueprint("administrator", __name__, url_prefix="/admin")

@bp.route("/today", methods=("GET", "POST"))
@login_required
def today():
    db = get_db()
    today = date.today()
    #tomorrow = date.today()
    tomorrow = today + timedelta(days=1)
    #formatted_today = today.strftime("%Y-%m-%d %H:%M:%S")
    #formatted_tomo = tomorrow.strftime("%Y-%m-%d %H:%M:%S")
    formatted_today = today.strftime("%Y-%m-%d 00:00:00")
    formatted_tomo = tomorrow.strftime("%Y-%m-%d 00:00:00")
    trades = db.execute(
        "SELECT *"
        " FROM stock s JOIN user u ON u.id = s.user_id"
        " WHERE added BETWEEN ? AND ?"
        " ORDER BY added DESC",
        (formatted_today, formatted_tomo)
    ).fetchall()
    print(trades)
    db.commit()
    symbols_traded = db.execute(
        "SELECT DISTINCT symbol, name"
        " FROM stock s JOIN user u ON u.id = s.user_id"
        " WHERE added BETWEEN ? AND ?"
        " ORDER BY added DESC",
        (formatted_today, formatted_tomo)
    ).fetchall()
    db.commit()

    shares_bought = {}
    shares_sold = {}

    for i in trades:
        if i["act"] == "buy":
            if i["symbol"] in shares_bought:
                shares_bought[i["symbol"]] += i["share"]
            else:
                shares_bought[i["symbol"]] = i["share"]
        elif i["act"] == "sell":
            if i["symbol"] in shares_sold:
                shares_sold[i["symbol"]] += i["share"]
            else:
                shares_sold[i["symbol"]] = i["share"]
    return render_template("administrator/today.html", trades_of_today=trades, symbols=symbols_traded, shares_s=shares_sold, shares_b=shares_bought)


def get_overall_share_balance(symbol):
    """Get the # of shares holded for a ticker specified in a trade for the current user."""
    shares_bought = (
        get_db()
        .execute(
            "SELECT SUM(s.share)"
            " FROM stock s JOIN user u ON u.id=s.user_id"
            " WHERE s.act = ? and s.symbol = ?",
            ("buy",symbol,),
        )
        .fetchone()
    )

    shares_sold  = (
        get_db()
        .execute(
            "SELECT SUM(s.share)"
            " FROM stock s JOIN user u ON u.id=s.user_id"
            " WHERE s.act = ? and s.symbol = ?",
            ("sell",symbol,),
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


def get_overall_portfolio():
    # get user's holding stocks and weights
    db = get_db()
    trades = db.execute(
        "SELECT DISTINCT symbol"
        " FROM stock s JOIN user u ON u.id = s.user_id"
        " ORDER BY added DESC"
    ).fetchall()
    
    stocks = list()
    for stock in trades:
       stocks.append(stock[0])

    
    shares = {}
    for symbol in stocks:
        shares[symbol] = get_overall_share_balance(symbol)

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

# ===========Pie Chart Starts==================


@bp.route('/get_pie', methods=['POST'])
def get_pie_data():
    db = get_db()

    data = db.execute(
        "SELECT DISTINCT symbol"
        " FROM stock"
    ).fetchall()

    # Convert the data to a list of dictionaries
    data_dict = []
    for row in data:
        shares = get_overall_share_balance(row['symbol'])
        if shares == 0:
            continue
        else:
            value = get_current_price(row['symbol'])*shares
            data_dict.append({'Symbol': row['symbol'], 'Value': value})


    return jsonify(data_dict)


# ===========Pie Chart Ends==================


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

    return render_template("administrator/account.html", user_info = user_info)


# ===========EF Graph Starts==================

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

    portfolio = get_overall_portfolio()

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

        # check if returns have the same length as others
        if len(returns_df) != 0:
            if len(returns) != len(returns_df):
                returns = returns[:len(returns_df)]
        # combine these returns into a pandas dataframe
        returns_df[symbol] = returns

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
        a_vol = np.std(returns_df[i]) * np.sqrt(255) # calculate annualized vol for each stock
        df_new_row = pd.DataFrame({'returns': avg_returns[i], 'vol': a_vol}, index=[0])
        rv = pd.concat([rv, df_new_row])
        # rv = rv.append({'returns': avg_returns[i], 'vol': a_vol}, ignore_index=True)

    # construct pf for portfolio_analyze() function
    pf = [sharpe_ratio, port_return, port_vol]

    # combine the two
    answer = {'rv': rv, 'pf': pf, 'cov': annual_cov}

    return answer


def optimize_risk(covar, expected_r, R):
    # Define objective function
    def objective(w):
        return w @ covar @ w.T

    # Define constraints
    constraints = [
        {"type": "eq", "fun": lambda w: np.sum(w) - 1},
        {"type": "eq", "fun": lambda w: expected_r @ w - R},
    ]

    # Define bounds
    bounds = [(0, None)] * len(expected_r)

    # Define initial guess
    x0 = np.full(len(expected_r), 1/len(expected_r))

    # Use minimize function to solve optimization problem
    result = minimize(objective, x0, method="SLSQP", bounds=bounds, constraints=constraints)

    # Return the objective value (risk) and the portfolio weights
    return {"risk": result.fun, "weights": result.x, "R": R}


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


@bp.route("/ef", methods=("GET", "POST"))
def ef():
    db = get_db()

    tickers = db.execute(
        "SELECT distinct symbol"
        " FROM stock s "
    ).fetchall()

    stock_num = len(tickers)

    pf = get_rv()['pf']

    return render_template("administrator/ef.html", stock_num = stock_num, pf = pf)


# ===========EF Graph Ends==================

@bp.route("/overview", methods=("GET", "POST"))
@login_required
def overview():

    db = get_db()

    symbols = db.execute(
        "SELECT DISTINCT symbol"
        " FROM stock s JOIN user u ON u.id = s.user_id"
        " ORDER BY added DESC"
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
        shares = get_overall_share_balance(i)
        if shares == 0:
            continue
        else:
            share_balance[i] = shares
    
    #get_rv(): answer = {'rv': rv, 'pf': pf, 'cov': annual_cov} / pf = [sharpe_ratio, port_return, port_vol]
    pf = get_rv()['pf']
    
    return render_template("administrator/overview.html", names=names, current_prices=current_prices, share_balance=share_balance, pf = pf)