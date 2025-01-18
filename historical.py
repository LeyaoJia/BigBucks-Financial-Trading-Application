import datetime
import requests
from Bigbucks.config import api_key
from Bigbucks.db import get_db

# function to retrieve daily adjusted historical data for a stock from Alpha Vantage API
def get_stock_data(symbol):
    url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol="+symbol+"&outputsize=full&apikey="+api_key
    response = requests.get(url)
    data = response.json()
    return data

def get_10year_yield():
    url = "https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=daily&maturity=10year&apikey="+api_key
    response = requests.get(url)
    data = response.json()
    return data


# function to store historical stock data in SQLite database
def store_stock_data(data):
    db = get_db()
    latest_date = max(data['Time Series (Daily)'].keys())
    latest_date_datetime = datetime.datetime.strptime(latest_date, '%Y-%m-%d')
    # Check if data of a stock on a specific date already exists in database
    extra_data = db.execute("SELECT * FROM HistData WHERE Date = ? AND symbol = ?", (latest_date_datetime.date(), data["Meta Data"]["2. Symbol"]
))
    row = extra_data.fetchone()
    if row:
        return
    
    # Check if data of a specific stock already exists in database
    row1 = db.execute("SELECT * FROM HistData WHERE symbol = ?", (data["Meta Data"]["2. Symbol"][0])).fetchone()
    if row1:
        ind = 0
        latest_date_db = db.execute("""
                                    SELECT MAX(date) AS latest_date
                                    FROM HistData
                                    WHERE symbol = ?;
                                    """, (data["Meta Data"]["2. Symbol"][0],)
                                    ).fetchall()
        while latest_date_db != datetime.datetime.strptime(data['Time Series (Daily)'].keys()[ind]).date():
            latest_data = data['Time Series (Daily)'][data['Time Series (Daily)'].keys()[ind]]
            db.execute('INSERT OR IGNORE INTO HistData (symbol, date, close) VALUES (?, ?, ?)',
                        (data["Meta Data"]["2. Symbol"], datetime.datetime.strptime(data['Time Series (Daily)'].keys()[ind]).date(), float(latest_data['5. adjusted close'])))
            db.execute('SELECT * FROM HistData ORDER BY date DESC')
            db.commit()
            ind += 1
        return

    # if conditions above are not met, then store the last five years' data into the database
    row2 = db.execute("SELECT DISTINCT symbol FROM HistData").fetchall()
    if row2:
        bottom_line_time_db = db.execute("""
                                    SELECT MIN(date) AS earliest_date
                                    FROM HistData
                                    """
                                    ).fetchall()
        bottom_line_time = datetime.datetime.strptime(bottom_line_time_db[0][0], '%Y-%m-%d').date()
    else:    
        bottom_line_time = latest_date_datetime.date() - datetime.timedelta(days=5*365)
    filtered_data = {date: values for date, values in data['Time Series (Daily)'].items() if datetime.datetime.strptime(date, '%Y-%m-%d').date() >= bottom_line_time}
    for date, values in filtered_data.items():
        # convert date string to datetime object
        date_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
        # insert row into database
        db.execute('INSERT OR IGNORE INTO HistData (symbol, date, close) VALUES (?, ?, ?)',
                    (data["Meta Data"]["2. Symbol"], date_obj.date(), float(values['5. adjusted close'])))
    
    db.commit()



# main function to retrieve and store last five years of daily adjusted historical data for a stock
def collect_stock_data(symbol):
    # get stock data from API
    stock_data = get_stock_data(symbol)
    # store data in database
    store_stock_data(stock_data)
