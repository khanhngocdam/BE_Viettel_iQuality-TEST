from fastapi import APIRouter
from .anomaly_detection import ping

router = APIRouter()

router.include_router(ping.router)

