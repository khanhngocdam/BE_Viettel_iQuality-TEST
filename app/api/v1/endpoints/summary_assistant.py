from openai import OpenAI
import os
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.services.get_kpi_data import get_internet_kpi_data, get_internet_kpi_change_data, AggregateLevel
from app.services.promt_summay import promt_internet_kpi_general, promt_kpi_change
from dotenv import load_dotenv

# Load your API key from .env file
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("Missing OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)
router = APIRouter(tags=["Summary-Assistant"])

@router.get("/summary-assistant/{aggregate_level}")
def summary_internet_kpi(
    aggregate_level: AggregateLevel,
    isp: str = Query(..., description="ISP"),
    kpi_code: str = Query(..., description="KPI code"),
    date_hour: str = Query(..., description="Date and hour"),
    db: Session = Depends(get_db)
):
    try:
        # Get KPI data
        result_general = get_internet_kpi_data(
            aggregate_level=aggregate_level,
            kpi_code=kpi_code,
            location_level="network",
            duration=1,
            db=db
        )

        # Get KPI change data
        result_change = get_internet_kpi_change_data(
            aggregate_level=aggregate_level,
            isp=isp,
            kpi_code=kpi_code,
            date_hour=date_hour,
            db=db
        )
        # Create the prompt (theo tuần hoặc theo ngày tùy aggregate_level)
        promt_general = "Bối cảnh chung về 3 nhà mạng:\n" + promt_internet_kpi_general(
            result_general, aggregate_level
        )
        promt_change = promt_kpi_change(result_change, kpi_code, isp, aggregate_level)
        promt_result = promt_general + promt_change

        # Call OpenRouter's model
        response = client.chat.completions.create(
            model="arcee-ai/trinity-large-preview:free",
            messages=[
                {"role": "system", "content": "Bạn là chuyên gia phân tích dữ liệu trong lĩnh vực hệ thống mạng."},
                {"role": "user", "content": promt_result},
            ]
        )

        # Return the model's response (not the prompt)
        return {"data": response.choices[0].message.content, "promt_result": promt_result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
