from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.deps import get_db
import logging

router = APIRouter(tags=["log_aggregate_data"])
logger = logging.getLogger(__name__)

@router.get("/log-aggregate-data")
def get_internet_kpi(
    aggregate_level: str = Query(..., description="Aggregate level"),
    kpi_code: str = Query(..., description="KPI code"),
    account_login_vqt: str = Query(..., description="Account login VQT"),
    server_name: str = Query(..., description="Server name"),
    duration: int = Query(1, ge=1, le=90, description="Duration"),
    db: Session = Depends(get_db)
):
    table_map = {
        "average_latency": "log_data_aggregate.ping_results_aggregate",
        "jitter": "log_data_aggregate.ping_results_aggregate",
        "packet_loss_rate": "log_data_aggregate.ping_results_aggregate",
        "dns_time": "log_data_aggregate.dns_results_aggregate",
        "data_downloading": "log_data_aggregate.dlul_results_aggregate",
        "web_browsing": "log_data_aggregate.web_results_size_load_aggregate",
    }

    table = table_map.get(kpi_code)
    if not table:
        raise HTTPException(status_code=400, detail=f"Unsupported kpi_code: {kpi_code}")

    try:
        sql = text(f"""
            SELECT *
            FROM {table}
            WHERE testing_time >= NOW() - (:duration || ' days')::interval
              AND account_login_vqt LIKE :account_login_vqt
              AND server_name = :server_name
              AND aggregate_level = :aggregate_level
            ORDER BY testing_time
        """)

        params = {
            "duration": duration,
            "aggregate_level": aggregate_level,
            "account_login_vqt": f"{account_login_vqt}_Agent%",
            "server_name": server_name,
        }
        result = db.execute(sql, params).mappings().all()

        return {
            "success": True,
            "aggregate_level": aggregate_level,
            "total": len(result),
            "data": result
        }

    except Exception:
        logger.exception(
            "Query failed",
            extra={"kpi_code": kpi_code, "aggregate_level": aggregate_level, "server_name": server_name, "duration": duration}
        )
        raise HTTPException(status_code=500, detail="Internal server error")
