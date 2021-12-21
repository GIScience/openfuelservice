import pathlib
from typing import Dict, Generator

import pytest
import pytest_alembic
import sqlalchemy
from fastapi.testclient import TestClient
from pytest_alembic.runner import MigrationContext
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session

from alembic.config import Config
from app import crud, schemas
from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app
from app.tests.utils.user import authentication_token_from_email
from app.tests.utils.utils import (
    get_token_headers_by_login,
    random_email,
    random_lower_string,
)

script_location = pathlib.Path(__file__).parent.resolve()


@pytest.fixture(scope="session")
def db() -> Generator:
    yield SessionLocal()


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def super_user(db: Session) -> Generator:
    user = crud.user.get_by_email(db, email=settings.FIRST_SUPERUSER)
    if not user:
        user_in = schemas.UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.user.create(db, obj_in=user_in)  # noqa: F841
    yield user, settings.FIRST_SUPERUSER_PASSWORD
    crud.user.remove(db, id=user.id)


@pytest.fixture(scope="session")
def normal_user(db: Session) -> Generator:
    user = crud.user.get_by_email(db, email=settings.EMAIL_TEST_USER)
    random_password = random_lower_string()
    if not user:
        user_in = schemas.UserCreate(
            email=settings.EMAIL_TEST_USER,
            password=random_password,
            is_superuser=False,
        )
        user = crud.user.create(db, obj_in=user_in)  # noqa: F841
    yield user, random_password
    crud.user.remove(db, id=user.id)


@pytest.fixture(scope="function")
def random_user_1(db: Session) -> Generator:
    username = random_email()
    password = random_lower_string()
    user_in = schemas.UserCreate(email=username, password=password)
    user = crud.user.create(db, obj_in=user_in)
    yield user, password
    crud.user.remove(db, id=user.id)


@pytest.fixture(scope="function")
def random_user_2(db: Session) -> Generator:
    username = random_email()
    password = random_lower_string()
    user_in = schemas.UserCreate(email=username, password=password)
    user = crud.user.create(db, obj_in=user_in)
    yield user, password
    crud.user.remove(db, id=user.id)


@pytest.fixture(scope="function")
def superuser_token_headers(client: TestClient, super_user: tuple) -> Dict[str, str]:
    return get_token_headers_by_login(client, super_user[0].email, super_user[1])


@pytest.fixture(scope="function")
def normal_user_token_headers(
    client: TestClient, db: Session, normal_user: tuple
) -> Dict[str, str]:
    return authentication_token_from_email(
        client=client, email=normal_user[0].email, db=db
    )


@pytest.fixture
def alembic_config() -> Config:
    alembic_config = Config(f"{script_location}/../../alembic.ini")
    alembic_config.set_main_option(
        "script_location", f"{script_location}/../../alembic"
    )
    return alembic_config


@pytest.fixture
def alembic_engine() -> Engine:
    """Override this fixture to provide pytest-alembic
    powered tests with a database handle."""

    return sqlalchemy.create_engine(
        settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True
    )


@pytest.fixture
def alembic_runner(alembic_config: Config, alembic_engine: Engine) -> MigrationContext:
    """Produce the primary alembic migration context in which to execute alembic tests.

    This fixture allows authoring custom tests which are specific to your particular
    migration history.
    """
    config = pytest_alembic.config.Config.from_raw_config(alembic_config)
    with pytest_alembic.runner(config=config, engine=alembic_engine) as runner:
        yield runner
