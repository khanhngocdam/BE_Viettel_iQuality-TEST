from sqlalchemy import text
from sqlalchemy.orm import Session
from enum import Enum
from datetime import datetime
from typing import Optional


class AggregateLevel(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


def get_internet_kpi_data(
    aggregate_level: AggregateLevel,
    kpi_code: str,
    location_level: str,
    duration: int,
    db: Session,
    time_limit: Optional[datetime] = None,
):
    table_map = {
        AggregateLevel.daily: "internet_kpi.internet_kpi_daily",
        AggregateLevel.weekly: "internet_kpi.internet_kpi_weekly",
        AggregateLevel.monthly: "internet_kpi.internet_kpi_monthly",
    }

    table = table_map[aggregate_level]

    try:
        sql = text(f"""
                SELECT *
                FROM {table}
                WHERE to_timestamp(date_hour, 'YYYY-MM-DD-HH24')
                    >= COALESCE(:time_limit, NOW()) - (:months || ' months')::interval
                AND kpi_code = :kpi_code AND location_level = :location_level
                ORDER BY to_timestamp(date_hour, 'YYYY-MM-DD-HH24') DESC
            """)
        result = db.execute(
            sql,
            {"kpi_code": kpi_code, "months": duration, "location_level": location_level, "time_limit": time_limit,}
        ).mappings().all()

        return result

    except Exception:
        raise Exception("Internal server error")


def get_internet_kpi_change_data(
    aggregate_level: AggregateLevel,
    isp: str,
    kpi_code: str,
    date_hour: str,
    db: Session
):
    table_map = {
        AggregateLevel.daily: "internet_kpi.internet_kpi_daily_change",
        AggregateLevel.weekly: "internet_kpi.internet_kpi_weekly_change",
        AggregateLevel.monthly: "internet_kpi.internet_kpi_monthly_change",
    }

    table = table_map[aggregate_level]

    try:
        sql = text(f"""
                SELECT * from {table}
                WHERE kpi_code = :kpi_code
                AND isp = :isp
                AND location_level = 'province'
                AND date_hour  = :date_hour                 
                ORDER BY ABS(change_value) DESC;
            """)
        result = db.execute(
            sql,
            {"kpi_code": kpi_code, "date_hour": date_hour, "isp": isp}
        ).mappings().all()

        return result

    except Exception:
        raise Exception("Internal server error")
