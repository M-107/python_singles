import json
from datetime import datetime
from pathlib import Path

import click
import seaborn as sns
from matplotlib import pyplot as plt


class TranactionTypes:
    pay_in = "Incoming payment"
    pay_out = "Outgoing payment"
    pay_card = "Card payment"
    cash_withdraw = "Cash withdrawal"
    cash_deposit = "Cash deposit"
    refund = "Refund"


ttypes = TranactionTypes


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


def file2data(file: Path) -> list[Transaction]:
    transactions = []
    with open(file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        json_data = json.loads(line)
        transactions.append(Transaction(data_json=json_data))
    return transactions


def data2days(data: list[Transaction]) -> list[Day]:
    days = []
    current_day = data[0].date_paid
    current_day_list = [data[0]]
    for transaction in data[1:]:
        day = transaction.date_paid
        if day == current_day:
            current_day_list.append(transaction)
        else:
            days.append(
                Day(
                    date=current_day,
                    transactions=current_day_list,
                )
            )
            current_day = transaction.date_paid
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


def transactions_with_detail(
    transactions: list[Transaction], detail_string: str
) -> list[Transaction]:
    return [
        tr
        for tr in transactions
        if tr.details is not None and detail_string in tr.details
    ]


def get_payments_by_type(
    transactions: list[Transaction], transaction_type: str | list[str]
) -> list[Transaction]:
    if isinstance(transaction_type, str):
        transaction_type = [transaction_type]
    return [tr for tr in transactions if tr.payment_type in transaction_type]


def graph_xy(
    name: str,
    data_x: list,
    data_y: list,
    label_x: str,
    label_y: str,
    save_dir: Path | None = None,
):
    sns.set_theme()
    sns.set_style("whitegrid")
    plt.plot(data_x, data_y)
    plt.xlim(min(data_x), max(data_x))
    plt.ylim(min(data_y), max(data_y))
    plt.title(name)
    plt.xlabel(label_x)
    plt.ylabel(label_y)
    if save_dir:
        plt.gcf().set_size_inches(16, 9)
        plt.savefig(save_dir, dpi=300)
        plt.close()
    else:
        mng = plt.get_current_fig_manager()
        mng.window.state("zoomed")
        plt.show()


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
def main(input_file):
    input_file = Path(input_file).resolve()
    print(f"Analyzing file {input_file.stem}")
    transaction_list = file2data(file=input_file)
    days = data2days(data=transaction_list)
    months = data2months(data=transaction_list)
    print(
        f"Found {len(transaction_list)} transactions from {len(days)} days ({len(months)} months)"
    )
    for month in months:
        print("---")
        print(f"--- {month.date}")
        print("---")
        tr_out = get_payments_by_type(
            transactions=month.transactions,
            transaction_type=[ttypes.pay_out, ttypes.pay_card, ttypes.cash_withdraw],
        )
        for tr in tr_out:
            print(tr.details)


if __name__ == "__main__":
    main()
