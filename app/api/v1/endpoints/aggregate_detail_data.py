# app/api/aggregate_detail_data.py
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.services import get_data
from app.services.get_data import get_aggregate_data, KPICode
from app.core.deps import get_db

router = APIRouter(tags=["aggregate_detail_data"])

@router.get("/aggregate-detail-data/{kpi_code}")
def get_aggregate_detail_data(
    kpi_code: KPICode,
    aggregate_level: str = Query(..., description="Aggregate level"),
    prev_date: str = Query(..., description="Previous date"),
    current_date: str = Query(..., description="Current date"),   
    isp: str = Query(..., description="ISP"),
    account_login_vqt: str = Query(..., description="Account login VQT"),
    db: Session = Depends(get_db)
):
    try:
        result = get_aggregate_data(
            kpi_code=kpi_code,
            aggregate_level=aggregate_level,
            prev_date=prev_date,
            current_date=current_date,
            isp=isp,
            account_login_vqt=account_login_vqt,
            db=db
        )

        return {
            "success": True,
            "total": len(result),
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
