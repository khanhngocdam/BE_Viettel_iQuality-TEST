from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.deps import get_db
import traceback

router = APIRouter(tags=["Create-report"])

@router.get("/create-report-daily")
def create_report(
    date_hour : str = Query(..., description="Report date"),
    db: Session = Depends(get_db)
):
    try:
        sql = text("""
                SELECT *
                FROM internet_kpi.internet_kpi_daily
                WHERE date_hour = :date_hour
                AND location_level = 'network'
            """)
        result = db.execute(
            sql,
            {"date_hour": date_hour}
        ).mappings().all()

        return {
            "success": True,
            "date_hour": date_hour,
            "total": len(result),
            "data": result
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))