from datetime import datetime

import pytest

from app.services.date_time_parse import parse_time_key
from app.services.get_kpi_data import AggregateLevel


def test_parse_daily_today_uses_now_hour():
    now = datetime(2026, 2, 6, 13, 45, 0)
    assert parse_time_key("hôm nay", AggregateLevel.daily, now=now) == "2026-02-06-13"


def test_parse_daily_explicit_date_defaults_00_hour():
    now = datetime(2026, 2, 6, 13, 45, 0)
    assert parse_time_key("2026-02-01", AggregateLevel.daily, now=now) == "2026-02-01-00"


def test_parse_daily_dmy_format():
    now = datetime(2026, 2, 6, 13, 45, 0)
    assert parse_time_key("01/02/2026", AggregateLevel.daily, now=now) == "2026-02-01-00"


def test_parse_weekly_from_date():
    # 2026-02-06 is ISO week 6 of 2026
    now = datetime(2026, 2, 6, 13, 45, 0)
    assert parse_time_key("2026-02-06", AggregateLevel.weekly, now=now) == "W06-2026"


def test_parse_monthly_unsupported():
    now = datetime(2026, 2, 6, 13, 45, 0)
    with pytest.raises(ValueError):
        parse_time_key("2026-02-06", AggregateLevel.monthly, now=now)

