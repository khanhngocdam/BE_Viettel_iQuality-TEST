from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from app.services.get_kpi_data import AggregateLevel


_DATE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # 2026-02-06 or 2026/02/06
    (re.compile(r"(?P<y>\d{4})[/-](?P<m>\d{1,2})[/-](?P<d>\d{1,2})"), "ymd"),
    # 06/02/2026 or 06-02-2026
    (re.compile(r"(?P<d>\d{1,2})[/-](?P<m>\d{1,2})[/-](?P<y>\d{4})"), "dmy"),
]


def _extract_date(text: str, now: datetime) -> date:
    t = text.strip().lower()

    if not t or "hôm nay" in t or t in {"today", "nay"}:
        return now.date()
    if "hôm qua" in t or t == "yesterday":
        return (now - timedelta(days=1)).date()
    if "hôm kia" in t:
        return (now - timedelta(days=2)).date()
    if "ngày mai" in t or t == "tomorrow":
        return (now + timedelta(days=1)).date()

    for pattern, kind in _DATE_PATTERNS:
        m = pattern.search(t)
        if not m:
            continue
        y = int(m.group("y"))
        mo = int(m.group("m"))
        d = int(m.group("d"))
        # kind hiện tại không cần dùng vì group đã thống nhất tên
        _ = kind
        return datetime(year=y, month=mo, day=d).date()

    # fallback: không parse được -> dùng today
    return now.date()


def _extract_hour(text: str) -> int | None:
    t = text.strip().lower()

    # 2026-02-06-13
    m = re.search(r"\b\d{4}-\d{1,2}-\d{1,2}-(?P<h>\d{1,2})\b", t)
    if m:
        h = int(m.group("h"))
        return h if 0 <= h <= 23 else None

    # 13h, 13 giờ
    m = re.search(r"\b(?P<h>\d{1,2})\s*(h|giờ)\b", t)
    if m:
        h = int(m.group("h"))
        return h if 0 <= h <= 23 else None

    # 13:00
    m = re.search(r"\b(?P<h>\d{1,2})\s*:\s*\d{2}\b", t)
    if m:
        h = int(m.group("h"))
        return h if 0 <= h <= 23 else None

    return None


def parse_time_key(
    user_text: str | None,
    aggregate_level: AggregateLevel,
    *,
    now: datetime | None = None,
) -> str:
    """
    Parse ngữ cảnh ngày/giờ từ input người dùng.

    - daily: trả về format 'YYYY-MM-DD-HH' (HH mặc định 00, riêng "hôm nay" không có giờ -> lấy giờ hiện tại)
    - weekly: trả về format 'Www-YYYY' theo ISO week (dùng ngày đã parse)
    """
    now_dt = now or datetime.now()
    text = (user_text or "").strip()

    date = _extract_date(text, now_dt)

    if aggregate_level == AggregateLevel.daily:
        hour = _extract_hour(text)
        if hour is None:
            hour = now_dt.hour if date == now_dt.date() else 0
        return f"{date.strftime('%Y-%m-%d')}-{hour:02d}"

    if aggregate_level == AggregateLevel.weekly:
        iso_year, iso_week, _ = date.isocalendar()
        return f"W{iso_week:02d}-{iso_year}"

    raise ValueError(f"Unsupported aggregate_level for chat tool: {aggregate_level}")

