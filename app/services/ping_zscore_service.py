import pandas as pd
from app.db.session import SessionLocal
from app.repositories.ping_results_repo import fetch_ping_data, save_to_sqlite


def detect_anomalies(
    df: pd.DataFrame,
    group_cols: list[str],
    metrics: list[str],
    window: int = 72,
    threshold: float = 3.5,
) -> pd.DataFrame:
    """
    Tính Z-score dựa trên cửa sổ trượt (sliding window) của `window` điểm TRƯỚC ĐÓ.
    Logic:
      - Group theo `group_cols`.
      - Với mỗi điểm t, lấy mean & std của [t-window, ..., t-1].
      - Z = (value_t - mean) / std.
      - Trả về các dòng có |Z| > threshold.
    """
    if df.empty:
        return df

    # 1. Sắp xếp dữ liệu để đảm bảo tính đúng đắn của rolling window
    df = df.sort_values(by=group_cols + ["testing_time"])

    # CHUYỂN ĐỔI SANG FLOAT (FIX LỖI Decimal - Float)
    for col in metrics:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype(float)

    # 2. Tính Mean & Std của cửa sổ trượt (dùng transform để giữ nguyên số dòng)
    # shift(1): Dịch xuống 1 dòng để window không bao gồm điểm hiện tại
    grouped = df.groupby(group_cols)[metrics]
    
    def rolling_stats(x):
        return x.shift(1).rolling(window=window, min_periods=window)

    means = grouped.transform(lambda x: rolling_stats(x).mean())
    stds = grouped.transform(lambda x: rolling_stats(x).std(ddof=0))

    # 3. Tính Z-score
    # replace(0, 1e-9): Tránh chia cho 0
    z_scores = (df[metrics] - means) / stds.replace(0, 1e-9)

    # # 4. Business Logic: Packet Loss < 0.1% thì coi là bình thường (Z=0)
    # if "mean_packet_loss_rate" in metrics:
    #     z_scores.loc[df["mean_packet_loss_rate"] < 0.1, "mean_packet_loss_rate"] = 0

    # 5. Lọc Anomalies (Nếu bất kỳ metric nào vượt ngưỡng)
    is_anomaly = z_scores.abs().gt(threshold).any(axis=1)
    result = df[is_anomaly].copy()

    # 6. Gắn thêm thông tin Z-score để debug/trace
    for m in metrics:
        result[f"{m}__z"] = z_scores.loc[is_anomaly, m]
        result[f"{m}__mean_hist"] = means.loc[is_anomaly, m]

    return result


def detect_anomaly_z_score():
    db = SessionLocal()
    try:
        # Cấu hình
        HISTORY_WINDOW = 72
        METRICS = ["mean_jitter", "mean_average_latency", "mean_packet_loss_rate"]
        GROUP_COLS = ["isp", "account_login_vqt", "server_name"]
        
        # Lấy dữ liệu (Lấy dư ra history_window giờ để tính toán cho điểm hiện tại)
        # Giả sử chạy cho thời điểm hiện tại hoặc fix cứng
        target_time = pd.to_datetime("2026-02-08 00:00:00.000") 
        fetch_from = target_time - pd.Timedelta(hours=HISTORY_WINDOW)

        df = fetch_ping_data(
            db=db,
            aggregate_level="hour",
            from_time=fetch_from,
        )

        if df.empty:
            print("No data found.")
            return

        # Gọi hàm tính toán ngắn gọn
        anomalies = detect_anomalies(
            df=df,
            group_cols=GROUP_COLS,
            metrics=METRICS,
            window=HISTORY_WINDOW,
            threshold=2
        )

        # Lưu kết quả
        save_to_sqlite(anomalies, "ping_anomaly_zscore")
        print(f"Found and saved {len(anomalies)} anomalies.")
        return anomalies

    finally:
        db.close()


if __name__ == "__main__":
    detect_anomaly_z_score()
