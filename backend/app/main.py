import contextlib
import io
import logging
from logging.config import dictConfig

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.api_v1.api import api_router
from app.core.config import LogConfig, settings

logging_config = LogConfig().dict()

dictConfig(logging_config)
logger = logging.getLogger(settings.PROJECT_NAME)
logger.info(f"{settings.PROJECT_NAME} ist staring")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=True if settings.DEBUG else False,
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
