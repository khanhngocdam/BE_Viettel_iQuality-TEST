import numpy as np
import pandas as pd
from app.db.session import SessionLocal
from app.repositories.ping_results_repo import fetch_ping_data, save_to_sqlite


def detect_anomalies_robust(
    df: pd.DataFrame,
    group_cols: list[str],
    metrics: list[str],
    window: int = 72,
    threshold: float = 3.5,
) -> pd.DataFrame:
    """
    Tính ROBUST Z-score dựa trên cửa sổ trượt (sliding window).
    Công thức: Z = (Value - Median) / (MAD * 1.4826)
    
    Logic:
      - Median: Trung vị của window 72 điểm trước đó.
      - MAD (Median Absolute Deviation): Trung vị của độ lệch tuyệt đối.
      - Hệ số 1.4826: Để scale MAD tương đương với Std trong phân phối chuẩn.
    """
    if df.empty:
        return df

    # 1. Sắp xếp dữ liệu
    df = df.sort_values(by=group_cols + ["testing_time"])

    # 2. Chuyển đổi sang float (Fix lỗi Decimal từ DB)
    for col in metrics:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype(float)

    # 3. Định nghĩa hàm tính MAD cho rolling window
    # MAD = median(|x - median(x)|)
    def calculate_mad(x):
        return np.median(np.abs(x - np.median(x)))

    grouped = df.groupby(group_cols)[metrics]

    # 4. Tính Rolling Stats
    # Lưu ý: .apply() chậm hơn .mean()/.std() vectorization, nhưng bắt buộc để tính MAD chuẩn
    # raw=True giúp tăng tốc độ bằng cách dùng numpy array thay vì pandas series
    
    # Hàm helper để tạo rolling object dịch chuyển 1 bước (không bao gồm điểm hiện tại)
    def get_rolling(x):
        return x.shift(1).rolling(window=window, min_periods=window)

    medians = grouped.transform(lambda x: get_rolling(x).median())
    
    # Tính MAD
    mads = grouped.transform(lambda x: get_rolling(x).apply(calculate_mad, raw=True))

    # 5. Tính Robust Z-score
    # Scale MAD: MAD * 1.4826 ~ Sigma
    sigma_robust = mads * 1.4826
    
    # Tránh chia cho 0 (nếu lịch sử phẳng lỳ -> MAD=0)
    z_scores = (df[metrics] - medians) / sigma_robust.replace(0, 1e-9)

    # 6. Business Logic: Packet Loss < 0.1% thì coi là bình thường
    # if "mean_packet_loss_rate" in metrics:
    #     z_scores.loc[df["mean_packet_loss_rate"] < 0.1, "mean_packet_loss_rate"] = 0

    # 7. Lọc Anomalies
    is_anomaly = z_scores.abs().gt(threshold).any(axis=1)
    result = df[is_anomaly].copy()

    # 8. Gắn thông tin debug
    for m in metrics:
        result[f"{m}__z_robust"] = z_scores.loc[is_anomaly, m]
        result[f"{m}__median_hist"] = medians.loc[is_anomaly, m]
        result[f"{m}__mad_hist"] = mads.loc[is_anomaly, m]

    return result


def run_detection():
    db = SessionLocal()
    try:
        # Cấu hình
        HISTORY_WINDOW = 120
        METRICS = ["mean_jitter", "mean_average_latency", "mean_packet_loss_rate"]
        GROUP_COLS = ["isp", "account_login_vqt", "server_name"]
        
        # Lấy dữ liệu
        target_time = pd.to_datetime("2026-02-07 00:00:00.000") 
        fetch_from = target_time - pd.Timedelta(hours=HISTORY_WINDOW)

        df = fetch_ping_data(
            db=db,
            aggregate_level="hour",
            from_time=fetch_from,
        )

        if df.empty:
            print("No data found.")
            return

        print(f"Processing {len(df)} rows...")
        
        # Gọi hàm tính toán Robust Z-score
        anomalies = detect_anomalies_robust(
            df=df,
            group_cols=GROUP_COLS,
            metrics=METRICS,
            window=HISTORY_WINDOW,
            threshold=2 # Threshold của Robust Z thường giữ nguyên hoặc cao hơn xíu so với Z thường
        )

        # Lưu kết quả
        save_to_sqlite(anomalies, "ping_anomaly_robust_zscore")
        print(f"Found and saved {len(anomalies)} anomalies (Robust Z-score).")
        return anomalies

    finally:
        db.close()


if __name__ == "__main__":
    run_detection()
