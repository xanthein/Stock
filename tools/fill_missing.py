#!/usr/bin/env python3
import sys
import time
import sqlite3
import datetime
import argparse

from twstock.stock import TWSEFetcher

SLEEP_SECONDS = 5


def parse_date(date_str: str) -> datetime.date:
    """Parse and validate a YYYY-MM-DD string. Raises ValueError if invalid."""
    try:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(
            f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD."
        )


def get_stock_codes(conn: sqlite3.Connection) -> list:
    """Return list of stock codes from all tables named table_% in the DB."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'table_%'"
    )
    return [row[0][len('table_'):] for row in cursor.fetchall()]


def date_exists(conn: sqlite3.Connection, code: str, date_str: str) -> bool:
    """Return True if table_{code} already has a row for date_str."""
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT 1 FROM table_{code} WHERE date = ?", (date_str,)
    )
    return cursor.fetchone() is not None


def datatuple_to_row(record, date_str: str):
    """
    Map a TWSEFetcher DATATUPLE to a DB insert tuple for the given date_str.
    Returns None if record.date does not match date_str.
    None OHLC values (trading halt) become 0.0.
    """
    if record.date.strftime('%Y-%m-%d') != date_str:
        return None
    return (
        date_str,
        record.open  if record.open  is not None else 0.0,
        record.high  if record.high  is not None else 0.0,
        record.low   if record.low   is not None else 0.0,
        record.close if record.close is not None else 0.0,
        record.capacity,
    )


def backfill_stock(
    conn: sqlite3.Connection,
    code: str,
    target_date: datetime.date,
    fetcher: TWSEFetcher,
) -> str:
    """
    For a single stock code, check if target_date is missing and fetch+insert if so.
    Returns: 'skipped' if date already present,
             'inserted' if record was found and inserted,
             'no_data'  if API had no record for that date (holiday/delisted).
    """
    date_str = target_date.strftime('%Y-%m-%d')

    if date_exists(conn, code, date_str):
        return 'skipped'

    data = fetcher.fetch(target_date.year, target_date.month, code)
    time.sleep(SLEEP_SECONDS)

    for record in data.get('data', []):
        row = datatuple_to_row(record, date_str)
        if row is not None:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO table_{code} "
                "(date, open_price, high_price, low_price, close_price, volume) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                row,
            )
            return 'inserted'

    return 'no_data'


def main():
    parser = argparse.ArgumentParser(
        description='Backfill missing TWSE stock data for a given date.'
    )
    parser.add_argument('date', help='Target date in YYYY-MM-DD format')
    parser.add_argument('db', help='Path to the SQLite database file')
    args = parser.parse_args()

    try:
        target_date = parse_date(args.date)
    except ValueError as e:
        parser.error(str(e))

    conn = sqlite3.connect(args.db)
    fetcher = TWSEFetcher()
    codes = get_stock_codes(conn)
    total = len(codes)

    counts = {'skipped': 0, 'inserted': 0, 'no_data': 0}
    for i, code in enumerate(codes, 1):
        result = backfill_stock(conn, code, target_date, fetcher)
        counts[result] += 1
        print(f"[{i}/{total}] {code}: {result}")

    conn.commit()
    conn.close()

    print(
        f"\nDone. "
        f"Skipped: {counts['skipped']}, "
        f"Inserted: {counts['inserted']}, "
        f"No data: {counts['no_data']}"
    )


if __name__ == '__main__':
    main()
