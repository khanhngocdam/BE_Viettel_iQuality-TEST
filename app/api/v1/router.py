from fastapi import APIRouter
from .endpoints import health
from .endpoints import internet_kpi_data
from .endpoints import aggregate_detail_data
from .endpoints import log_agggregate_data
from .endpoints import create_report
from .endpoints import summary_assistant
from .endpoints import chat_assistant
from app.api.v1.endpoints.router import router as anomaly_detection_router

router = APIRouter()

router.include_router(health.router)
router.include_router(internet_kpi_data.router)
router.include_router(aggregate_detail_data.router)
router.include_router(log_agggregate_data.router)
router.include_router(create_report.router)
router.include_router(anomaly_detection_router, prefix='/anomaly-detection')
router.include_router(summary_assistant.router)
router.include_router(chat_assistant.router)


