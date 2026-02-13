from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_db_sqlite
import traceback
from datetime import datetime, timedelta

router = APIRouter(tags=["ping"])

@router.get("/ping")
def get_data(
        aggregate_level: str = Query(..., description="Aggregate level"),
        kpi_code: str = Query(..., description="KPI Code"),
        account_login_vqt: str = Query(..., description="Account login VQT"),
        server_name: str = Query (..., description="Server name" ),
        duration: int = Query(1, ge=1, le=90, description="Duration"),
        db: Session = Depends(get_db_sqlite)
    ):
    kpi_code = 'mean_' + kpi_code
    try:
        # Tính toán thời gian bằng Python (Portable & Safe)
        from_time = datetime.now() - timedelta(days=duration)
        sql = text("""
                    SELECT *
                    FROM ping_anomaly_zscore
                    WHERE server_name = :server_name
                    AND testing_time >= :from_time   
                    AND aggregate_level = :aggregate_level
                    AND account_login_vqt LIKE :account_login_vqt
                    ORDER BY testing_time DESC;""")
        result = db.execute(sql, {
            "from_time": from_time,
            "aggregate_level": aggregate_level,
            "account_login_vqt": f"{account_login_vqt}_Agent%",
            "server_name": server_name
        }).mappings().all()
        return {
            "success": True,
            "total": len(result),
            "data": result
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metadata/servers")
def get_server_list(
    duration: int = Query(1, ge=1, le=90, description="Duration"),
    account_login_vqt: str = Query(..., description="Account login VQT"),
    db: Session = Depends(get_db)  # Use Postgres DB
):
    try:
        from datetime import datetime, timedelta
        
        # Calculate time in Python for portability
        from_time = datetime.now() - timedelta(days=duration)

        sql = text("""
            SELECT DISTINCT server_name 
            FROM log_data_aggregate.ping_results_aggregate 
            WHERE testing_time >= :from_time 
              AND server_name LIKE '%Speedtest' 
              AND account_login_vqt LIKE :account_login_vqt
            ORDER BY server_name ASC
        """)
        
        result = db.execute(sql, {
            "from_time": from_time,
            "account_login_vqt": f"{account_login_vqt}_Agent%",
        }).scalars().all()
        
        return {
            "success": True,
            "total": len(result),
            "data": result
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
