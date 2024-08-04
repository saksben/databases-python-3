import sqlite3
import datetime
import csv
from dataclasses import dataclass

import requests
import click

CREATE_INVESTMENTS_SQL = """
CREATE TABLE IF NOT EXISTS investments (
    coin_id TEXT,
    currency TEXT,
    amount REAL,
    sell INT, 
    date TIMESTAMP
);
"""

@dataclass
class Investment:
    coin_id: str
    currency: str
    amount: float
    sell: bool
    date: datetime.datetime

    def compute_value(self) -> float:
        return self.amount * get_coin_price(self.coin_id, self.currency)

# Creates a class that represents sql data model, so you can refer to values by name instead of position
def investment_row_factory(_, row):
    return Investment(
        coin_id = row[0],
        currency = row[1],
        amount = row[2],
        sell = bool(row[3]),
        date = datetime.datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S.%f")
    )
# Need to run e.g. >>python row_factories.py get-investment-values --coin_id=bitcoin --currency=usd

def get_coin_price(coin_id, currency):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={currency}"
    data = requests.get(url).json()
    coin_price = data[coin_id][currency]
    return coin_price

@click.group()
def cli():
    pass

@click.command()
@click.option("--coin_id", default="bitcoin")
@click.option("--currency", default="usd")
def show_coin_price(coin_id, currency):
    coin_price = get_coin_price(coin_id, currency)
    print(f"The price of {coin_id} is {coin_price:.2f} {currency.upper()}")

@click.command()
@click.option("--coin_id")
@click.option("--currency")
@click.option("--amount", type=float)
@click.option("--sell", is_flag=True)
def add_investment(coin_id, currency, amount, sell):
    sql = "INSERT INTO investments VALUES (?, ?, ?, ?, ?);"
    values = (coin_id, currency, amount, sell, datetime.datetime.now())
    cursor.execute(sql, values)
    database.commit()

    if sell:
        print(f"Added sell of {amount} {coin_id}")
    else:
        print(f"Added buy of {amount} {coin_id}")

@click.command()
@click.option("--coin_id")
@click.option("--currency")
def get_investment_value(coin_id, currency):
    coin_price = get_coin_price(coin_id, currency)
    sql = """SELECT *
    FROM investments
    WHERE coin_id=?
    AND currency=?
    AND sell=?;"""
    buy_result = cursor.execute(sql, (coin_id, currency, False)).fetchall()
    sell_result = cursor.execute(sql, (coin_id, currency, True)).fetchall()
    buy_amount = sum([row.amount for row in buy_result])
    sell_amount = sum([row.amount for row in sell_result])

    total = buy_amount - sell_amount

    print(f"You own a total of {total} {coin_id} worth {total * coin_price} {currency.upper()}")

@click.command()
@click.option("--csv_file")
def import_investments(csv_file):
    with open(csv_file, "r") as f:
        rdr = csv.reader(f, delimiter=",")
        rows = list(rdr)
        sql = "INSERT INTO investments VALUES (?, ?, ?, ?, ?);"
        cursor.executemany(sql, rows)
        database.commit()

        print(f"Imported {len(rows)} investments from {csv_file}")

cli.add_command(show_coin_price)
cli.add_command(add_investment)
cli.add_command(get_investment_value)
cli.add_command(import_investments)

if __name__ == "__main__":
    database = sqlite3.connect("portfolio.db")
    database.row_factory = investment_row_factory
    cursor = database.cursor()
    cursor.execute(CREATE_INVESTMENTS_SQL)
    cli()
