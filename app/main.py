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
        allow_origins=["*"],
        allow_credentials=True,   # dùng nếu FE gửi cookie / auth
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # =================

    app.include_router(api_router)
    return app


app = create_app()
