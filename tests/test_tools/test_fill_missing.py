import sys
import sqlite3
import datetime
from collections import namedtuple
from unittest.mock import MagicMock, patch
import pytest

from pathlib import Path

# 1. Find the absolute path to the root 'scripts' directory
# __file__ is this test file. .parents[2] climbs up to the project root.
tools_path = str(Path(__file__).resolve().parents[2] / "tools")

# 2. Inject it into Python's search paths if it isn't already there
if tools_path not in sys.path:
    sys.path.insert(0, tools_path)

import fill_missing
from fill_missing import (
    parse_date,
    get_stock_codes,
    date_exists,
    datatuple_to_row,
    backfill_stock,
)

# Local DATATUPLE matching twstock's namedtuple structure exactly
DATATUPLE = namedtuple(
    'Data',
    ['date', 'capacity', 'turnover', 'open', 'high', 'low', 'close',
     'change', 'transaction', 'note'],
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_test_db():
    """Return an in-memory SQLite connection with two sample stock tables."""
    conn = sqlite3.connect(':memory:')
    for code in ('2330', '0050'):
        conn.execute(
            f"CREATE TABLE table_{code} "
            "(date STRING, open_price REAL, high_price REAL, "
            "low_price REAL, close_price REAL, volume INTEGER)"
        )
    conn.commit()
    return conn


# ── parse_date ────────────────────────────────────────────────────────────────

def test_parse_date_valid():
    result = parse_date('2026-06-03')
    assert result == datetime.date(2026, 6, 3)


def test_parse_date_wrong_order():
    with pytest.raises(ValueError, match="Invalid date format"):
        parse_date('06-03-2026')


def test_parse_date_not_a_date():
    with pytest.raises(ValueError, match="Invalid date format"):
        parse_date('not-a-date')


# ── get_stock_codes / date_exists ─────────────────────────────────────────────

def test_get_stock_codes_returns_all_codes():
    conn = make_test_db()
    codes = get_stock_codes(conn)
    assert sorted(codes) == ['0050', '2330']
    conn.close()


def test_date_exists_when_present():
    conn = make_test_db()
    conn.execute(
        "INSERT INTO table_2330 VALUES ('2026-06-03', 100.0, 105.0, 99.0, 102.0, 1000000)"
    )
    conn.commit()
    assert date_exists(conn, '2330', '2026-06-03') is True
    conn.close()


def test_date_exists_when_absent():
    conn = make_test_db()
    assert date_exists(conn, '2330', '2026-06-03') is False
    conn.close()


# ── datatuple_to_row ──────────────────────────────────────────────────────────

def test_datatuple_to_row_matching_date():
    record = DATATUPLE(
        date=datetime.datetime(2026, 6, 3),
        capacity=1000000, turnover=500000,
        open=100.0, high=105.0, low=99.0, close=102.0,
        change=2.0, transaction=500, note='',
    )
    row = datatuple_to_row(record, '2026-06-03')
    assert row == ('2026-06-03', 100.0, 105.0, 99.0, 102.0, 1000000)


def test_datatuple_to_row_non_matching_date():
    record = DATATUPLE(
        date=datetime.datetime(2026, 6, 4),
        capacity=1000000, turnover=500000,
        open=100.0, high=105.0, low=99.0, close=102.0,
        change=2.0, transaction=500, note='',
    )
    row = datatuple_to_row(record, '2026-06-03')
    assert row is None


def test_datatuple_to_row_none_ohlc_becomes_zero():
    record = DATATUPLE(
        date=datetime.datetime(2026, 6, 3),
        capacity=0, turnover=0,
        open=None, high=None, low=None, close=None,
        change=0.0, transaction=0, note='',
    )
    row = datatuple_to_row(record, '2026-06-03')
    assert row == ('2026-06-03', 0.0, 0.0, 0.0, 0.0, 0)


# ── backfill_stock ────────────────────────────────────────────────────────────

def test_backfill_stock_skips_when_date_exists():
    conn = make_test_db()
    conn.execute(
        "INSERT INTO table_2330 VALUES ('2026-06-03', 100.0, 105.0, 99.0, 102.0, 1000000)"
    )
    conn.commit()
    mock_fetcher = MagicMock()
    with patch('time.sleep'):
        result = backfill_stock(conn, '2330', datetime.date(2026, 6, 3), mock_fetcher)
    assert result == 'skipped'
    mock_fetcher.fetch.assert_not_called()
    conn.close()


def test_backfill_stock_inserts_found_record():
    conn = make_test_db()
    record = DATATUPLE(
        date=datetime.datetime(2026, 6, 3),
        capacity=1000000, turnover=500000,
        open=100.0, high=105.0, low=99.0, close=102.0,
        change=2.0, transaction=500, note='',
    )
    mock_fetcher = MagicMock()
    mock_fetcher.fetch.return_value = {'stat': 'OK', 'data': [record]}
    with patch('time.sleep'):
        result = backfill_stock(conn, '2330', datetime.date(2026, 6, 3), mock_fetcher)
    assert result == 'inserted'
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM table_2330 WHERE date='2026-06-03'")
    row = cursor.fetchone()
    assert row == ('2026-06-03', 100.0, 105.0, 99.0, 102.0, 1000000)
    conn.close()


def test_backfill_stock_no_data_when_date_absent_from_response():
    conn = make_test_db()
    record = DATATUPLE(
        date=datetime.datetime(2026, 6, 4),
        capacity=1000000, turnover=500000,
        open=100.0, high=105.0, low=99.0, close=102.0,
        change=2.0, transaction=500, note='',
    )
    mock_fetcher = MagicMock()
    mock_fetcher.fetch.return_value = {'stat': 'OK', 'data': [record]}
    with patch('time.sleep'):
        result = backfill_stock(conn, '2330', datetime.date(2026, 6, 3), mock_fetcher)
    assert result == 'no_data'
    conn.close()


def test_backfill_stock_no_data_when_api_returns_empty():
    conn = make_test_db()
    mock_fetcher = MagicMock()
    mock_fetcher.fetch.return_value = {'stat': '', 'data': []}
    with patch('time.sleep'):
        result = backfill_stock(conn, '2330', datetime.date(2026, 6, 3), mock_fetcher)
    assert result == 'no_data'
    conn.close()


def test_backfill_stock_sleeps_after_api_call():
    conn = make_test_db()
    mock_fetcher = MagicMock()
    mock_fetcher.fetch.return_value = {'stat': '', 'data': []}
    with patch('time.sleep') as mock_sleep:
        backfill_stock(conn, '2330', datetime.date(2026, 6, 3), mock_fetcher)
    mock_sleep.assert_called_once_with(fill_missing.SLEEP_SECONDS)
    conn.close()


def test_backfill_stock_does_not_sleep_when_skipped():
    conn = make_test_db()
    conn.execute(
        "INSERT INTO table_2330 VALUES ('2026-06-03', 100.0, 105.0, 99.0, 102.0, 1000000)"
    )
    conn.commit()
    mock_fetcher = MagicMock()
    with patch('time.sleep') as mock_sleep:
        backfill_stock(conn, '2330', datetime.date(2026, 6, 3), mock_fetcher)
    mock_sleep.assert_not_called()
    conn.close()
