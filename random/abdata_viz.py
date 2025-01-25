import json
from datetime import datetime
from pathlib import Path

import click
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D


class TranactionTypes:
    pay_in = "Incoming payment"
    pay_out = "Outgoing payment"
    pay_card = "Card payment"
    cash_withdraw = "Cash withdrawal"
    cash_deposit = "Cash deposit"
    refund = "Refund"


ttypes = TranactionTypes
ttypes_out = [ttypes.pay_out, ttypes.pay_card, ttypes.cash_withdraw]
ttypes_in = [ttypes.pay_in, ttypes.cash_deposit, ttypes.refund]


class Transaction:
    def __init__(self, data_json: dict) -> None:
        self.date_posted = datetime.strptime(data_json["date_posted"], "%d.%m.%Y")
        self.date_paid = datetime.strptime(data_json["date_paid"], "%d.%m.%Y")
        self.payment_type = data_json["payment_type"]
        self.transaction_id = int(data_json["transaction_id"])
        self.account_holder = data_json["account_holder"]
        self.account_number = data_json["account_or_card_number"]
        self.details = data_json["details"]
        self.ammount = round(
            float(str(data_json["ammount"]).replace(" ", "").replace(",", ".")), 2
        )
        self.fee = round(
            float(str(data_json["fee"]).replace(" ", "").replace(",", ".")), 2
        )


class Day:
    def __init__(self, date: datetime, transactions: list[Transaction]) -> None:
        self.date = date
        self.transactions = transactions


class Month:
    def __init__(self, date: datetime, transactions: list[Transaction]) -> None:
        self.date = date
        self.transactions = transactions


def file2transactions(file: Path) -> list[Transaction]:
    transactions = []
    with open(file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        json_data = json.loads(line)
        transactions.append(Transaction(data_json=json_data))
    return transactions


def data2days(data: list[Transaction]) -> list[Day]:
    days = []
    current_day = data[0].date_posted
    current_day_list = [data[0]]
    for transaction in data[1:]:
        day = transaction.date_posted
        if day == current_day:
            current_day_list.append(transaction)
        else:
            days.append(
                Day(
                    date=current_day,
                    transactions=current_day_list,
                )
            )
            current_day = transaction.date_posted
            current_day_list = [transaction]
    return days


def data2months(data: list[Transaction]) -> list[Month]:
    months = []
    current_month = datetime.strftime(data[0].date_paid, "%Y-%m")
    current_month_list = [data[0]]
    for transaction in data[1:]:
        month = datetime.strftime(transaction.date_paid, "%Y-%m")
        if month == current_month:
            current_month_list.append(transaction)
        else:
            months.append(
                Month(
                    date=datetime.strptime(current_month, "%Y-%m"),
                    transactions=current_month_list,
                )
            )
            current_month = datetime.strftime(transaction.date_paid, "%Y-%m")
            current_month_list = [transaction]
    return months


def payments_by_type(
    transactions: list[Transaction], transaction_type: str | list[str]
) -> list[Transaction]:
    if isinstance(transaction_type, str):
        transaction_type = [transaction_type]
    return [tr for tr in transactions if tr.payment_type in transaction_type]


def total_balance_each_day(days: list[Day]) -> list[float]:
    balance_list = []
    current_balance = 0
    for day in days:
        current_balance += sum([tr.ammount for tr in day.transactions])
        balance_list.append(current_balance)
    return balance_list


def daily_changes(days: list[Day]) -> list[float]:
    daily_changes = []
    for day in days:
        daily_change = sum(transaction.ammount for transaction in day.transactions)
        daily_changes.append(daily_change)
    return daily_changes


def manual_cleanup_helpers(transaction_list: list[Transaction]) -> None:
    WHITE = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    print("---")
    for transaction in transaction_list:
        if transaction.ammount > 1000 or transaction.ammount < -1000:
            print(
                f"{RED if transaction.ammount < 0 else GREEN}{transaction.ammount:>15,.2f}{WHITE} [{transaction.date_paid.date()}] {transaction.details}"
            )
    print("---")
    for transaction in transaction_list:
        if transaction.details is not None:
            if transaction.details[-1] == " " or transaction.details[-1].isdigit():
                print(
                    f"{RED if transaction.ammount < 0 else GREEN}{transaction.ammount:>15,.2f}{WHITE} [{transaction.date_paid.date()}] [{transaction.payment_type}] {transaction.details}"
                )
    print("---")
    bad_transactions_out = [
        transaction
        for transaction in transaction_list
        if transaction.payment_type in ttypes_out and transaction.ammount > 0
    ]
    bad_transactions_in = [
        transaction
        for transaction in transaction_list
        if transaction.payment_type in ttypes_in and transaction.ammount < 0
    ]
    print(f"Bad transactions out: {len(bad_transactions_out)}")
    print(f"Bad transactions in: {len(bad_transactions_in)}")
    print("---")
    print("Unknown transaction types:")
    for transaction in transaction_list:
        if transaction.payment_type not in ttypes_in + ttypes_out:
            print(
                f"{RED if transaction.ammount < 0 else GREEN}{transaction.ammount:>15,.2f}{WHITE} [{transaction.date_paid.date()}] [{transaction.payment_type}] {transaction.details}"
            )
    print("---")


def graph_all(days: list[Day]) -> None:
    sns.set_theme()
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.set_xlim([days[0].date, days[-1].date])

    dates = [day.date for day in days]
    total_balance = total_balance_each_day(days)
    ax1.plot(dates, total_balance, color="#1f77b4", label="Total Balance")
    ax1.fill_between(dates, total_balance, color="#1f77b4", alpha=0.3)
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Total Balance", color="#1f77b4")
    ax1.tick_params(axis="y", labelcolor="#1f77b4")
    ax1.grid()

    ax2 = ax1.twinx()
    changes = daily_changes(days)
    colors = ["green" if change > 0 else "red" for change in changes]
    ax2.bar(dates, changes, color=colors, alpha=0.6, label="Daily Change")
    ax2.set_ylabel("Daily Change", color="black")
    ax2.tick_params(axis="y", labelcolor="black")

    fig.suptitle("Total Balance and Daily Changes Over Time")
    fig.tight_layout()
    custom_lines = [
        Line2D([0], [0], color="green", lw=4),
        Line2D([0], [0], color="red", lw=4),
        Line2D([0], [0], color="#1f77b4", lw=2),
    ]
    fig.legend(
        custom_lines,
        ["Daily Change (Positive)", "Daily Change (Negative)", "Total Balance"],
        loc="upper left",
        bbox_to_anchor=(0.1, 0.9),
    )
    plt.show()


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
def main(input_file):
    input_file = Path(input_file).resolve()
    print(f"Analyzing file {input_file.stem}")
    transaction_list = file2transactions(file=input_file)
    days = data2days(data=transaction_list)
    print(
        f"Found {len(transaction_list)} transactions from {len(days)} days over the span of {round((days[-1].date - days[0].date).days / 365.25, 1)} years"
    )
    total_income = sum(
        [tr.ammount for tr in transaction_list if tr.payment_type in ttypes_in]
    )
    total_expenses = sum(
        [tr.ammount for tr in transaction_list if tr.payment_type in ttypes_out]
    )
    WHITE = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    print(f"Total income: {GREEN}{total_income:,.2f}{WHITE}".replace(",", " "))
    print(f"Total expenses: {RED}{total_expenses:,.2f}{WHITE}".replace(",", " "))
    net = total_income + total_expenses
    print(f"Net income: {GREEN if net > 0 else RED}{net:,.2f}{WHITE}".replace(",", " "))
    graph_all(days=days)


if __name__ == "__main__":
    main()
