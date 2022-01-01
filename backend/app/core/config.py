import logging
import os
import pathlib
import secrets
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import AnyHttpUrl, BaseSettings, EmailStr, HttpUrl, PostgresDsn, validator

script_location = pathlib.Path(__file__).parent.resolve()
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    SERVER_NAME: str
    SERVER_HOST: AnyHttpUrl
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    BACKEND_CORS_ORIGINS: Union[str, List[AnyHttpUrl]]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str
    SENTRY_DSN: Optional[HttpUrl] = None

    @validator("SENTRY_DSN", pre=True)
    def sentry_dsn_can_be_blank(cls, v: str) -> Optional[str]:
        if len(v) == 0:
            return None
        return v

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER", "db"),
            port=values.get("POSTGRES_PORT", "5432"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None

    @validator("EMAILS_FROM_NAME")
    def get_project_name(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if not v:
            return values["PROJECT_NAME"]
        return v

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    EMAIL_TEMPLATES_DIR: str = "/app/app/email-templates/build"
    EMAILS_ENABLED: bool = False

    @validator("EMAILS_ENABLED", pre=True)
    def get_emails_enabled(cls, v: bool, values: Dict[str, Any]) -> bool:
        return bool(
            values.get("SMTP_HOST")
            and values.get("SMTP_PORT")
            and values.get("EMAILS_FROM_EMAIL")
        )

    EMAIL_TEST_USER: EmailStr = "test@example.com"  # type: ignore
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str
    USERS_OPEN_REGISTRATION: bool = False

    CELERY_BROKER_URL: str = "amqp://guest@queue//"

    FILE_FOLDER: str = f"{script_location}/../files/"

    # category_list
    CAR_CATEGORIES: Dict = {}

    @validator("CAR_CATEGORIES", pre=True)
    def get_car_categories(cls, v: Optional[str], values: Dict[str, Any]) -> Dict:
        try:
            return yaml.safe_load(
                open(
                    f"{values['FILE_FOLDER']}/internal/categories.yml", encoding="utf-8"
                )
            )
        except Exception:
            logger.error("Couldn't read car categories from file.")
            return {}

    # car_brands
    CAR_BRANDS: Dict = {}

    @validator("CAR_BRANDS", pre=True)
    def get_car_brands(cls, v: Optional[str], values: Dict[str, Any]) -> Dict:
        try:
            return yaml.safe_load(
                open(
                    f"{values['FILE_FOLDER']}/internal/car_brands.yml", encoding="utf-8"
                )
            )
        except Exception:
            logger.error("Couldn't car brands from file.")
            return {}

    # fixed_matches
    FIXED_MATCHES: Dict = {}

    @validator("FIXED_MATCHES", pre=True)
    def get_fixed_matches(cls, v: Optional[str], values: Dict[str, Any]) -> Dict:
        try:
            return yaml.safe_load(
                open(
                    f"{values['FILE_FOLDER']}/internal/fixed_matches.yml",
                    encoding="utf-8",
                )
            )
        except Exception:
            logger.error("Couldn't car brands from file.")
            return {}

    # allowed_fuel_types
    ENABLED_FUEL_TYPES: List[str] = ["gasoline", "diesel"]

    # CARFUELDATA_PATH_OR_URL: str = "https://carfueldata.vehicle-certification-agency.gov.uk/downloads/create_latest_data_csv.asp?id=6"  # noqa: E501
    CARFUELDATA_PATH_OR_URL: str = f"{FILE_FOLDER}/carfueldata/Euro_6_latest_22-12-2021.zip"
    CARFUELDATA_TEST_PATH_OR_URL: str = f"{FILE_FOLDER}/test_data/cfd_test_file.zip"

    class Config:
        DEBUGGING_CONFIG: str = os.getenv("DEBUGGING_CONFIG", "")
        case_sensitive = True
        if DEBUGGING_CONFIG is not None and len(DEBUGGING_CONFIG):
            env_file = DEBUGGING_CONFIG

    # Country Data
    COUNTRY_CODES_PATH: str = f"{FILE_FOLDER}/country/country_codes.csv"
    COUNTRY_CODES_ATTRIBUTION: str = "Made with Natural Earth. Free vector and raster map data @ naturalearthdata.com"
    COUNTRY_BOUNDARIES_PATH: str = f"{FILE_FOLDER}/country/TM_WORLD_BORDERS-0.3.zip"
    COUNTRY_BOUNDARIES_ATTRIBUTION: str = "https://thematicmapping.org/downloads/world_borders.php"


settings = Settings()
