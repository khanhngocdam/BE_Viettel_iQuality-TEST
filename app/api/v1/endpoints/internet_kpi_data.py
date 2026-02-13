from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.services.get_kpi_data import get_internet_kpi_data, get_internet_kpi_change_data, AggregateLevel

router = APIRouter(tags=["internet_kpi_data"])

@router.get("/internet-kpi/{aggregate_level}")
def get_internet_kpi(
    aggregate_level: AggregateLevel,
    kpi_code: str = Query(..., description="KPI code"),
    location_level: str = Query(..., description="Location level"),
    duration: int = Query(1, ge=1, le=24, description="Duration in months (1-24)"),
    db: Session = Depends(get_db)
):
    try:
        # Gọi hàm từ service để lấy dữ liệu
        result = get_internet_kpi_data(
            aggregate_level=aggregate_level,
            kpi_code=kpi_code,
            location_level=location_level,
            duration=duration,
            db=db
        )

        return {
            "success": True,
            "aggregate_level": aggregate_level,
            "kpi_code": kpi_code,
            "total": len(result),
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/internet-kpi/{aggregate_level}/change")
def get_internet_kpi_change(
    aggregate_level: AggregateLevel,
    isp: str = Query(..., description="ISP"),
    kpi_code: str = Query(..., description="KPI code"),
    date_hour: str = Query(..., description="Date and hour"),
    db: Session = Depends(get_db)
):
    try:
        # Gọi hàm từ service để lấy dữ liệu
        result = get_internet_kpi_change_data(
            aggregate_level=aggregate_level,
            isp=isp,
            kpi_code=kpi_code,
            date_hour=date_hour,
            db=db
        )

        return {
            "success": True,
            "aggregate_level": aggregate_level,
            "kpi_code": kpi_code,
            "isp": isp,
            "total": len(result),
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
