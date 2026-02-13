# app/services.py
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.deps import get_db
from enum import Enum
import traceback


class KPICode(str, Enum):
    latency = "internet_latency"
    jitter = "internet_jitter"
    packet_loss_rate = "internet_packetloss"
    dns_time = "internet_dns_time"
    data_downloading = "internet_data_downloading"
    web_browsing = "internet_web_browsing"


def get_aggregate_data(
    kpi_code: KPICode,
    aggregate_level: str,
    prev_date: str,
    current_date: str,
    isp: str,
    account_login_vqt: str,
    db: Session
):
    table_map = {
        KPICode.latency: "log_data_aggregate.ping_results_aggregate",
        KPICode.jitter: "log_data_aggregate.ping_results_aggregate",
        KPICode.packet_loss_rate: "log_data_aggregate.ping_results_aggregate",
        KPICode.dns_time: "log_data_aggregate.dns_results_aggregate",
        KPICode.data_downloading: "log_data_aggregate.dlul_results_aggregate",
        KPICode.web_browsing: "log_data_aggregate.web_results_size_load_aggregate",
    }
    table = table_map[kpi_code]
    
    kpi_map = {
        KPICode.latency: "average_latency",
        KPICode.jitter: "jitter",
        KPICode.packet_loss_rate: "packet_loss_rate",
        KPICode.dns_time: "resolve_duration_ms",
        KPICode.data_downloading: "download_speed_mbps",
        KPICode.web_browsing: "load_time_0_5mb_ms",
    }
    kpi_column = f"mean_{kpi_map[kpi_code]}"

    server_col_map = {
        KPICode.latency: "server_name",
        KPICode.jitter: "server_name",
        KPICode.packet_loss_rate: "server_name",
        KPICode.dns_time: "dns_server_isp",
        KPICode.data_downloading: "server_info",
        KPICode.web_browsing: "request_url",
    }
    server_col = server_col_map[kpi_code]

    try:
        sql = text(f"""
                SELECT
                    t.{server_col},
                    t.aggregate_level,
                    t.account_login_vqt,
                    t.current_value,
                    t.previous_value,
                    (t.current_value - t.previous_value) AS different_value
                    FROM (
                    SELECT
                        {server_col},
                        aggregate_level,
                        account_login_vqt,
                        MAX(CASE WHEN testing_time = CAST(:current_date AS date)
                                THEN {kpi_column} END) AS current_value,
                        MAX(CASE WHEN testing_time = CAST(:prev_date AS date)
                                THEN {kpi_column} END) AS previous_value
                    FROM {table}
                    WHERE (testing_time = CAST(:current_date AS date) OR testing_time = CAST(:prev_date AS date))
                        AND aggregate_level = :aggregate_level
                        AND isp = :isp
                        AND account_login_vqt LIKE :account_login_vqt
                        
                    GROUP BY {server_col}, aggregate_level, account_login_vqt
                    ) t
                    WHERE t.current_value IS NOT NULL
                    AND t.previous_value IS NOT NULL;
                    """)

        result = db.execute(
            sql,
            {
                "current_date": current_date, 
                "prev_date": prev_date, 
                "isp": isp, "account_login_vqt": f"{account_login_vqt}_Agent%", 
                "aggregate_level": aggregate_level,
            }
        ).mappings().all()

        return result

    except Exception as e:
        traceback.print_exc()
        raise Exception(str(e))
