import sqlite3
import datetime
import csv

import requests
import click

# Create db
CREATE_INVESTMENTS_SQL = """
CREATE TABLE IF NOT EXISTS investments (
    coin_id TEXT,
    currency TEXT,
    amount REAL,
    sell INT, 
    date TIMESTAMP
);
"""

# Run the functions in your command line (see examples under each function)

# Get a coin price via the CoinGecko API
def get_coin_price(coin_id, currency):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={currency}" # CoinGecko API
    data = requests.get(url).json() # Request the API data
    coin_price = data[coin_id][currency] # Search the data response for the coin price
    return coin_price

@click.group()
def cli():
    pass

# Fetch the current coin price of a given coin and currency (default is bitcoin in usd)
# Notice the flags to determine parameters in the command line (see the example of what to run)
@click.command()
@click.option("--coin_id", default="bitcoin")
@click.option("--currency", default="usd")
def show_coin_price(coin_id, currency):
    coin_price = get_coin_price(coin_id, currency)
    print(f"The price of {coin_id} is {coin_price:.2f} {currency.upper()}")
# Need to run e.g. >>python main.py show-coin-price --coin_id=ethereum

# Add an investment of a given amount into a given coin using a given currency, either a buy or sell
@click.command()
@click.option("--coin_id")
@click.option("--currency")
@click.option("--amount", type=float)
@click.option("--sell", is_flag=True)
def add_investment(coin_id, currency, amount, sell):
    sql = "INSERT INTO investments VALUES (?, ?, ?, ?, ?);" # Make command to execute a sql query
    values = (coin_id, currency, amount, sell, datetime.datetime.now()) # Use the parameteres as values when the function is called
    cursor.execute(sql, values) # Execute query
    database.commit() # Commit to db

    if sell:
        print(f"Added sell of {amount} {coin_id}")
    else:
        print(f"Added buy of {amount} {coin_id}")
# Need to run e.g. >>python main.py add-investment --coin_id=bitcoin --currency=usd --amount=1.0
# OR >>python main.py add-investment --coin_id=bitcoin --currency=usd --amount=1.0 --sell

# Show the user's equity in a given coin in a given currency
@click.command()
@click.option("--coin_id")
@click.option("--currency")
def get_investment_value(coin_id, currency):
    coin_price = get_coin_price(coin_id, currency) # Get the coin price
    # Fetch the buying and selling amounts from the db
    sql = """SELECT amount
    FROM investments
    WHERE coin_id=?
    AND currency=?
    AND sell=?;"""
    buy_result = cursor.execute(sql, (coin_id, currency, False)).fetchall() # Execute the sql query for buy values
    sell_result = cursor.execute(sql, (coin_id, currency, True)).fetchall() # Execute the sql query for sell values
    buy_amount = sum([row[0] for row in buy_result])
    sell_amount = sum([row[0] for row in sell_result])

    total = buy_amount - sell_amount

    print(f"You own a total of {total} {coin_id} worth {total * coin_price} {currency.upper()}")
# Need to run e.g. >>python main.py get-investment-value --coin_id=bitcoin --currency=usd

# Import coin transaction data from a given csv file
@click.command()
@click.option("--csv_file")
def import_investments(csv_file):
    with open(csv_file, "r") as f: # Open a csv file to read
        rdr = csv.reader(f, delimiter=",") # Parse through the csv after every ","
        rows = list(rdr) # Make a list of csv rows from the parsed data
        sql = "INSERT INTO investments VALUES (?, ?, ?, ?, ?);"
        cursor.executemany(sql, rows) # Execute the sql query to add the data to the db
        database.commit()

        print(f"Imported {len(rows)} investments from {csv_file}")
# Need to run e.g. >>python main.py import-investments --csv_file investments.csv

# Functions you can run in the terminal
cli.add_command(show_coin_price)
cli.add_command(add_investment)
cli.add_command(get_investment_value)
cli.add_command(import_investments)

if __name__ == "__main__":
    database = sqlite3.connect("portfolio.db") # Connect to db
    cursor = database.cursor()  # Create a db cursor
    cursor.execute(CREATE_INVESTMENTS_SQL) # Create the table
    cli()

