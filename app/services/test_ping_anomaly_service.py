import numpy as np
import pandas as pd
from app.db.session import SessionLocal
from app.repositories.ping_results_repo import fetch_ping_data, save_to_sqlite


def add_robust_zscore(
    df: pd.DataFrame,
    group_cols: list[str],
    time_col: str,
    metrics: list[str],
    history_points: int = 24,
    eps: float = 1e-9,
    z_threshold: float = 3.5,
) -> pd.DataFrame:

    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.sort_values(group_cols + [time_col])

    def rolling_mad(x):
        return np.nanmedian(np.abs(x - np.nanmedian(x)))

    out = []

    for _, g in df.groupby(group_cols, sort=False):
        g = g.sort_values(time_col).copy()

        z_cols = []

        for m in metrics:
            x = pd.to_numeric(g[m], errors="coerce")

            med = x.rolling(history_points).median().shift(1)
            mad = x.rolling(history_points).apply(rolling_mad, raw=True).shift(1)

            z = 0.6745 * (x - med) / mad.where(mad > eps)

            col_z = f"{m}__robust_z"
            g[col_z] = z
            g[f"{m}__median_hist"] = med
            g[f"{m}__mad_hist"] = mad
            z_cols.append(col_z)

        g_anomaly = g.loc[
            g[z_cols].abs().gt(z_threshold).any(axis=1)
        ]

        if not g_anomaly.empty:
            out.append(g_anomaly)

    if not out:
        return df.iloc[0:0].copy()

    return pd.concat(out).sort_values(group_cols + [time_col])



def detect_anomaly_robust_z_score():
    db = SessionLocal()
    history_points = 24
    try:
        from_time = pd.to_datetime("2026-01-19 15:00:00.000")

        fetch_from = from_time - pd.Timedelta(hours=history_points)
        df = fetch_ping_data(
            db=db,
            aggregate_level="hour",
            from_time=fetch_from,
        )
        if df.empty:
            print("No data returned from DB.")
            return df
        time_col = "testing_time"
        group_cols = ["isp", "account_login_vqt", "server_name"]
        metrics = ["mean_jitter", "mean_average_latency", "mean_packet_loss_rate"]
        # ---------------------------------------------

        missing = [c for c in [time_col, *group_cols, *metrics] if c not in df.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}. Current columns: {df.columns.tolist()}")

        scored = add_robust_zscore(
            df=df,
            group_cols=["isp", "account_login_vqt", "server_name"],
            time_col="testing_time",
            metrics=metrics,
            history_points=history_points,
        )
        print(len(scored))
        # Save the scored data to the database
        save_to_sqlite(scored, "ping_anomaly_scores")

    finally:
        db.close()


if __name__ == "__main__":
    detect_anomaly_robust_z_score()
