import json
from datetime import datetime
from decimal import Decimal
from os import environ
from pathlib import Path

import click
import psycopg2
from psycopg2.extras import DictCursor

DB_DSN = environ.get("DB_DSN_TH", None)
if not DB_DSN:
    raise ValueError("Please set the DB_DSN_TH environment variable.")


def parse_cz_date(s: str | None):
    if not s:
        return None
    return datetime.strptime(s, "%d.%m.%Y").date()


def parse_cz_amount(s: str | None) -> Decimal:
    if s is None:
        return Decimal("0")
    s = s.replace(" ", "").replace(",", ".")
    return Decimal(s)


def get_or_create_account(cur, account_number: str, account_holder: str | None):
    cur.execute(
        """
        INSERT INTO account (account_number, account_holder)
        VALUES (%s, %s)
        ON CONFLICT (account_number)
        DO UPDATE SET
            account_holder = COALESCE(account.account_holder, EXCLUDED.account_holder)
        RETURNING id;
        """,
        (account_number, account_holder),
    )
    return cur.fetchone()[0]


OUTGOING_TYPES = {
    "Outgoing payment",
    "Cash withdrawal",
    "Card payment",
}

INCOMING_TYPES = {
    "Incoming payment",
    "Cash deposit",
    "Refund",
}


def get_or_create_payment_type(cur, name: str | None, amount_raw: Decimal):
    if not name:
        is_outgoing = amount_raw < 0
        name = "Unknown outgoing" if is_outgoing else "Unknown incoming"
    else:
        if name in OUTGOING_TYPES:
            is_outgoing = True
        elif name in INCOMING_TYPES:
            is_outgoing = False
        else:
            is_outgoing = amount_raw < 0
    cur.execute(
        """
        INSERT INTO payment_type (name, is_outgoing)
        VALUES (%s, %s)
        ON CONFLICT (name)
        DO UPDATE SET
            is_outgoing = EXCLUDED.is_outgoing
        RETURNING id;
        """,
        (name, is_outgoing),
    )
    return cur.fetchone()[0]


def import_jsonl(input_file: Path):
    conn = psycopg2.connect(DB_DSN)
    conn.autocommit = False
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            with open(input_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    date_posted = parse_cz_date(data.get("date_posted"))
                    date_paid = parse_cz_date(data.get("date_paid"))
                    payment_type_str = data.get("payment_type")
                    amount_raw = parse_cz_amount(data.get("ammount"))
                    fee_raw = parse_cz_amount(data.get("fee"))
                    payment_type_id = get_or_create_payment_type(
                        cur, payment_type_str, amount_raw
                    )
                    bank_transaction_id = int(data.get("transaction_id"))
                    account_holder = data.get("account_holder")
                    counterparty_account_number = data.get("account_or_card_number")
                    note = data.get("details")
                    counterparty_id = None
                    if counterparty_account_number:
                        counterparty_id = get_or_create_account(
                            cur,
                            counterparty_account_number,
                            account_holder,
                        )
                    amount = abs(amount_raw)
                    fee = abs(fee_raw)
                    cur.execute(
                        """
                        INSERT INTO transaction (
                            date_posted,
                            date_paid,
                            payment_type_id,
                            counterparty_account_id,
                            amount,
                            fee,
                            currency,
                            note,
                            bank_transaction_id
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, 'CZK', %s, %s)
                        ON CONFLICT (bank_transaction_id) DO NOTHING;
                        """,
                        (
                            date_posted,
                            date_paid,
                            payment_type_id,
                            counterparty_id,
                            amount,
                            fee,
                            note,
                            bank_transaction_id,
                        ),
                    )
                    if line_num % 100 == 0:
                        print(f"Imported {line_num} lines...")
            conn.commit()
            print("Import finished.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
def main(input_file):
    import_jsonl(input_file=Path(input_file))


if __name__ == "__main__":
    main()
