import pandas as pd
import traceback
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy import create_engine


def fetch_ping_data(
    db: Session,
    aggregate_level: str,
    from_time,
) -> pd.DataFrame:
    try:
        sql = text("""
            SELECT * 
            FROM log_data_aggregate.ping_results_aggregate
            WHERE testing_time >= :from_time
              AND aggregate_level = :aggregate_level
        """)

        result = (
            db.execute(
                sql,
                {"from_time": from_time, "aggregate_level": aggregate_level}
            )
            .mappings()
            .all()
        )

        return pd.DataFrame(result)

    except Exception as e:
        traceback.print_exc()
        # raise lại exception gốc
        raise


def save_to_sqlite(df: pd.DataFrame, table_name: str = "ping_anomaly"):
    engine = create_engine("sqlite:///ping_results.db")

    for c in df.select_dtypes(include="object").columns:
        try:
            df[c] = pd.to_numeric(df[c])
        except Exception:
            pass  # giữ nguyên cột text

    df.to_sql(table_name, engine, if_exists="replace", index=False)

