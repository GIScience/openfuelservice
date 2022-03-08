import json
import os
import pathlib
import secrets
import tarfile
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import (
    AnyHttpUrl,
    BaseModel,
    BaseSettings,
    EmailStr,
    HttpUrl,
    PostgresDsn,
    validator,
)
from requests_toolbelt import user_agent

script_location = pathlib.Path(__file__).parent.resolve()


class Settings(BaseSettings):
    # Testing settings
    # USE_CONTAINER_TESTING_DB: bool = True

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
    DEBUG: bool = True
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
    TEST_FILE_FOLDER: str = f"{script_location}/../files/"

    # category_list
    CAR_CATEGORIES: Dict = {}

    @validator("CAR_CATEGORIES", pre=True)
    def get_car_categories(cls, v: Optional[str], values: Dict[str, Any]) -> Dict:
        return yaml.safe_load(
            open(f"{values['FILE_FOLDER']}/internal/categories.yml", encoding="utf-8")
        )

    # car_brands
    CAR_BRANDS: Dict = {}

    @validator("CAR_BRANDS", pre=True)
    def get_car_brands(cls, v: Optional[str], values: Dict[str, Any]) -> Dict:
        return yaml.safe_load(
            open(f"{values['FILE_FOLDER']}/internal/car_brands.yml", encoding="utf-8")
        )

    # fixed_matches
    FIXED_MATCHES: Dict = {}

    @validator("FIXED_MATCHES", pre=True)
    def get_fixed_matches(cls, v: Optional[str], values: Dict[str, Any]) -> Dict:
        return json.load(
            open(
                f"{values['FILE_FOLDER']}/internal/fixed_matches.json",
                encoding="utf-8",
            )
        )

    ENABLED_FUEL_TYPES: List[str] = ["gasoline", "diesel"]

    # CARFUELDATA_PATH_OR_URL: str = "https://carfueldata.vehicle-certification-agency.gov.uk/downloads/create_latest_data_csv.asp?id=6"  # noqa: E501
    CARFUELDATA_PATH_OR_URL: str = (
        f"{FILE_FOLDER}/carfueldata/Euro_6_latest_22-12-2021.zip"
    )
    CARFUELDATA_TEST_PATH_OR_URL: str = f"{FILE_FOLDER}/carfueldata/cfd_test_file.zip"

    class Config:
        DEBUGGING_CONFIG: str = os.getenv("DEBUGGING_CONFIG", "")
        case_sensitive = True
        if DEBUGGING_CONFIG is not None and len(DEBUGGING_CONFIG):
            env_file = DEBUGGING_CONFIG

    # Country Data
    COUNTRY_CODES_PATH: str = f"{FILE_FOLDER}/countrydata/country_codes.csv"
    COUNTRY_CODES_TEST_PATH: str = f"{FILE_FOLDER}/countrydata/test_country_codes.csv"
    COUNTRY_CODES_ATTRIBUTION: str = "Made with Natural Earth. Free vector and raster map data @ naturalearthdata.com"
    COUNTRY_BOUNDARIES_PATH: str = f"{FILE_FOLDER}/countrydata/TM_WORLD_BORDERS-0.3.zip"
    COUNTRY_BOUNDARIES_TEST_PATH: str = (
        f"{FILE_FOLDER}/countrydata/TM_WORLD_BORDERS-0.3.zip"
    )
    COUNTRY_BOUNDARIES_ATTRIBUTION: str = (
        "https://thematicmapping.org/downloads/world_borders.php"
    )

    # Fueldata
    # EUROSTAT_FUEL_HISTORY_1994_2005: str = f"{FILE_FOLDER}/fuelprices/eurostat_time_series_years_1994_2005.zip"
    EUROSTAT_FUEL_HISTORY_2005_ONWARDS: str = "https://ec.europa.eu/energy/observatory/reports/Oil_Bulletin_Prices_History.xlsx"  # noqa: E501
    EUROSTAT_TEST_FUEL_HISTORY_2005_ONWARDS: str = f"{FILE_FOLDER}/fuelprices/eurostat_time_series_years_2005_2021.zip"  # noqa: E501
    EUROSTAT_FUEL_ATTRIBUTION: str = "European Union, 1995 - today"

    # Envirocar
    ENVIROCAR_BASE_URL: str = "https://envirocar.org/api/stable"
    TEST_ENVIROCAR_PHENOMENONS_RESPONSE: str = (
        f"{FILE_FOLDER}/envirocar/test_envircoar_phenomenons.json"
    )
    TEST_ENVIROCAR_SENSOR_ID_RESPONSE: str = (
        f"{FILE_FOLDER}/envirocar/test_envirocar_sensor_id_response.json"
    )
    TEST_ENVIROCAR_SENSORS_RESPONSE: str = (
        f"{FILE_FOLDER}/envirocar/test_envirocar_sensors_response.json"
    )
    TEST_ENVIROCAR_SENSORS_STATISTICS_RESPONSE: str = (
        f"{FILE_FOLDER}/envirocar/test_envirocar_sensors_statistics_response.json"
    )
    TEST_ENVIROCAR_TRACK_ID_RESPONSE: str = (
        f"{FILE_FOLDER}/envirocar/test_envirocar_track_id_response.json"
    )
    TEST_ENVIROCAR_TRACK_MEASUREMENT_RESPONSE: str = f"{FILE_FOLDER}/envirocar/test_envirocar_track_measurements_response.json"  # noqa: E501
    TEST_ENVIROCAR_TRACKS_RESPONSE: str = (
        f"{FILE_FOLDER}/envirocar/test_envirocar_tracks_response.json"
    )

    # Wikipedia
    TEST_WIKIPEDIA_KATEGORIE_KLEINSTWAGEN_RESPONSE: str = (
        f"{FILE_FOLDER}/wikipedia/test_kategorie_kleinstwagen_response.json"  # noqa
    )
    TEST_WIKIPEDIA_KATEGORIE_KLEINSTWAGEN_INFO_RESPONSE: str = f"{FILE_FOLDER}/wikipedia/test_kategorie_kleinstwagen_info_response.json"  # noqa
    TEST_WIKIPEDIA_KATEGORIE_LEICHTFAHRZEUGE_RESPONSE: str = (
        f"{FILE_FOLDER}/wikipedia/test_kategorie_leichtfahrzeug_response.json"  # noqa
    )
    TEST_WIKIPEDIA_KATEGORIE_LEICHTFAHRZEUGE_INFO_RESPONSE: str = f"{FILE_FOLDER}/wikipedia/test_kategorie_leichtfahrzeug_info_response.json"  # noqa
    TEST_WIKIPEDIA_CATEGORY_MICROCARS_RESPONSE: str = (
        f"{FILE_FOLDER}/wikipedia/test_category_microcars_response.json"
    )
    TEST_WIKIPEDIA_CATEGORY_MICROCARS_INFO_RESPONSE: str = (
        f"{FILE_FOLDER}/wikipedia/test_category_microcars_info_response.json"  # noqa
    )

    # User Agent header
    USER_AGENT = user_agent("Openfuelservice", "0.0.1")
    USER_AGENT_FROM = "julian.psotta@heigit.org"
    GLOBAL_HEADERS = {"User-Agent": USER_AGENT, "From": USER_AGENT_FROM}

    # Matching Settings
    UNCOMPRESSED_MATCHING_DATA: str = f"{FILE_FOLDER}/matching/models/"
    COMPRESSED_MATCHING_DATA: str = f"{FILE_FOLDER}/matching/models.tar.xz"

    # openrouteservice data
    OPENROUTESERVICE_EXAMPLE_REQUEST_HEIDELBERG: Dict = {}

    @validator("OPENROUTESERVICE_EXAMPLE_REQUEST_HEIDELBERG", pre=True)
    def get_openrouteservice_example_request(
        cls, v: Optional[str], values: Dict[str, Any]
    ) -> Dict:
        return json.load(
            open(
                f"{values['FILE_FOLDER']}/openrouteservice/openrouteservice_example_request_heidelberg.json",
                encoding="utf-8",
            )
        )

    @validator("COMPRESSED_MATCHING_DATA", pre=True)
    def uncompress_matching_data(cls, v: str, values: Dict[str, Any]) -> str:
        print("Uncompressing Matching data")
        compressed_model_path: pathlib.Path = pathlib.Path(v)
        uncomporessed_model_path = pathlib.Path(values["UNCOMPRESSED_MATCHING_DATA"])
        if not compressed_model_path.exists():
            raise ValueError(f"COMPRESSED_MATCHING_DATA doesn't exist: {v}")
        if not uncomporessed_model_path.exists():
            os.mkdir(uncomporessed_model_path)
        existing_models = [name for name in os.listdir(uncomporessed_model_path)]
        if len(existing_models) > 0:
            print(
                f"Found {len(existing_models)} models. Skip uncompressing. Delete them if you want to start fresh. | "
                f"Folder: {values['UNCOMPRESSED_MATCHING_DATA']}"
            )
            return v
        print(
            f"No models found. Starting model extraction to folder: {uncomporessed_model_path}"
        )
        with tarfile.open(v) as f:
            members = f.getmembers()
            print(f"Found {len(members)} models. Extracting them now.")
            for member in members:
                member.path = member.path.strip("models/")
                f.extract(member=member, path=uncomporessed_model_path)
            # f.extractall('.')
        existing_models = [
            name
            for name in os.listdir(uncomporessed_model_path)
            if os.path.isfile(name)
        ]
        print(
            f"Successfully extracted {existing_models} models to folder: {uncomporessed_model_path}"
        )
        return v


settings = Settings()


class LogConfig(BaseModel):
    """Logging configuration to be set for the server"""

    LOGGER_NAME: str = settings.PROJECT_NAME
    LOG_FORMAT: str = (
        f"%(asctime)s.%(msecs)d %(levelname)-8s [{settings.PROJECT_NAME}]"
        f"[%(filename)s:%(lineno)d] %(message)s"
    )
    COLOR_LOG_FORMAT = "%(log_color)s" + LOG_FORMAT

    LOG_LEVEL: str = "DEBUG" if settings.DEBUG else "INFO"

    # Logging config
    version = 1
    disable_existing_loggers = False
    colors = {
        "DEBUG": "green",
        "INFO": "white",
        "WARNING": "bold_yellow",
        "ERROR": "bold_red",
        "CRITICAL": "bold_purple",
    }
    formatters = {
        "default": {
            "()": "logging.Formatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "color": {
            "()": "colorlog.ColoredFormatter",
            "fmt": COLOR_LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "log_colors": colors,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers = {
        "default": {
            "formatter": "color",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "color",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "sqlalchemy": {
            "formatter": "color",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "alembic": {
            "formatter": "color",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    }
    loggers = {
        LOGGER_NAME: {"handlers": ["default"], "level": "INFO"},
        "uvicorn": {"handlers": ["default"], "level": "INFO"},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "propagate": False, "level": "INFO"},
    }
