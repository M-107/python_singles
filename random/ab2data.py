import csv
import json
import re
import sys
from pathlib import Path

import click
from pypdf import PdfReader, errors


def read_pdf(file: Path) -> list[str]:
    try:
        reader = PdfReader(stream=file)
    except errors.PdfStreamError:
        print("Failed to read the input file, make sure it is a valid PDF file.")
        sys.exit(1)
    num_pages = len(reader.pages)
    print(f"Found {num_pages} pages of data")
    text = ""
    for num in range(0, num_pages):
        page = reader.pages[num]
        text += page.extract_text()
    lines = text.split("\n")
    return lines


def cleanup_lines(lines: list[str]) -> list[str]:
    lines = lines[18:-7]
    pattern_junk = r"Pokra"
    matches_junk = [
        index for index, string in enumerate(lines) if re.match(pattern_junk, string)
    ]
    junk_lines = [number + i for number in matches_junk for i in range(8)]
    clean_lines = [line for index, line in enumerate(lines) if index not in junk_lines]
    pattern_transaction = r"^ \d{2}.\d{2}.\d{4}$"
    matches_transactions = [
        index
        for index, string in enumerate(clean_lines)
        if re.match(pattern_transaction, string)
    ]
    split_lines = [
        clean_lines[matches_transactions[i] : matches_transactions[i + 1]]
        for i in range(len(matches_transactions) - 1)
    ]
    split_lines.append(clean_lines[matches_transactions[-1] :])
    split_lines = [[line.strip() for line in lines] for lines in split_lines]
    split_strings = [" ".join(lines) for lines in split_lines]
    print(f"Found {len(split_strings)} transaction details")
    return split_strings


def lines_to_data(lines: list[str]) -> list[dict]:
    pattern_details = re.compile(
        r"^(?P<date_posted>\d{2}.\d{2}.\d{4})\s+(?P<date_paid>\d{2}.\d{2}.\d{4})\s+(?P<payment_type>Platba kartou|(?:Příchozí|Odchozí) úhrada|(?:Výběr|Vklad) hotovosti|Vrácení peněz)\s+(?P<transaction_id>\d{8,12})\s+(?:(?:(?P<account_holder>.*)(?:\s))?(?P<account_or_card_number>\d{6}\*{6}\d{4}|(?:\d*-)?\d{8,10} / \d{4}))\s+(?P<details>.*?)\s*?(?P<ammount>-?(?:\d{1,3} )*\d{1,3},\d{2})\s+(?P<fee>-?(\d{1,3} )*\d{1,3},\d{2})$"
    )
    dict_list = []
    for string in lines:
        match = pattern_details.match(string)
        if match:
            dict_list.append(match.groupdict())
    for transaction in dict_list:
        for key, value in transaction.items():
            if value == "":
                transaction[key] = None
            if key == "payment_type":
                cz_en_payment_types = {
                    "Příchozí úhrada": "Incoming payment",
                    "Odchozí úhrada": "Outgoing payment",
                    "Výběr hotovosti": "Cash withdrawal",
                    "Vklad hotovosti": "Cash deposit",
                    "Platba kartou": "Card payment",
                    "Vrácení peněz": "Refund",
                }
                transaction[key] = cz_en_payment_types[value]
    return dict_list


def save_all(file: Path, data: list[dict]):
    save_csv(file=file, data=data)
    save_json(file=file, data=data)
    save_jsonl(file=file, data=data)


def save_csv(file: Path, data: list[dict]):
    file_name = f"{file}.csv"
    print(f"Saving data to {file_name}")
    keys = data[0].keys()
    with open(file_name, "w", newline="", encoding="utf-8") as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)


def save_json(file: Path, data: list[dict]):
    file_name = f"{file}.json"
    print(f"Saving data to {file_name}")
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def save_jsonl(file: Path, data: list[dict]):
    file_name = f"{file}.jsonl"
    print(f"Saving data to {file_name}")
    with open(file_name, "w", encoding="utf-8") as f:
        for d in data:
            json_line = json.dumps(d, ensure_ascii=False)
            f.write(json_line + "\n")


save_options = {
    "all": None,
    "csv": save_csv,
    "json": save_json,
    "jsonl": save_jsonl,
}


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "-ft",
    "--file-type",
    required=True,
    multiple=True,
    type=click.Choice(save_options.keys()),
    help="What file type to save the resulting data in.",
)
def main(input_file, file_type):
    input_file = Path(input_file).resolve()
    print(f"Analyzing file {input_file.stem}")
    file_no_suffix = input_file.parent / input_file.stem
    lines_from_pdf = read_pdf(file=input_file)
    formatted_lines = cleanup_lines(lines=lines_from_pdf)
    dicts_from_lines = lines_to_data(lines=formatted_lines)
    if "all" in file_type:
        save_all(file=file_no_suffix, data=dicts_from_lines)
    else:
        for output_type in file_type:
            save_options[output_type](file=file_no_suffix, data=dicts_from_lines)


if __name__ == "__main__":
    main()
