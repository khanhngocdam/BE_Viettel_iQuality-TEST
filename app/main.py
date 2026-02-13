from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.router import router as api_router


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(title=settings.APP_NAME)

    # ===== CORS =====
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://171.243.228.60:1218",
            "http://192.168.10.240:3000",
        ],
        allow_credentials=True,   # dùng nếu FE gửi cookie / auth
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # =================

    app.include_router(api_router)
    return app


app = create_app()
