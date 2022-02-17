import json
import logging
import pathlib
from typing import AsyncGenerator, Dict, Generator, List

import pytest
import pytest_alembic
import responses
import sqlalchemy
from fastapi.testclient import TestClient
from httpx import AsyncClient
from pytest_alembic.runner import MigrationContext
from sqlalchemy import exc
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session

from alembic.config import Config
from app import crud, models, schemas
from app.core.config import settings
from app.db.base_class import Base
from app.db.importer.base_importer import BaseImporter
from app.db.importer.carfueldata.carfueldata_reader import CarFuelDataReader
from app.db.importer.wikipedia.wikipedia_reader import WikipediaReader
from app.db.session import SessionLocal, engine
from app.main import app
from app.models import CarFuelDataCar, WikiCarCategory
from app.tests.utils.envirocar import (
    create_random_sensor,
    create_random_track,
    create_random_track_measurement,
)
from app.tests.utils.user import authentication_token_from_email
from app.tests.utils.utils import (
    get_token_headers_by_login,
    random_email,
    random_lower_string,
)

script_location = pathlib.Path(__file__).parent.resolve()
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def db(alembic_runner: MigrationContext) -> Generator:
    # client = None
    # container_id = None
    # if settings.USE_CONTAINER_TESTING_DB:
    #     try:
    #         client = docker.APIClient(base_url='unix://var/run/docker.sock')
    #         logger.info("##################################################")
    #         logger.info("> Initializing containerized database for testing: ")
    #         logger.info(f"> Docker Version: {client.version()}")
    #         logger.info(f"> Docker API Version: {client.api_version}")
    #         logger.info(f"> Docker image: postgis/postgis:12-3.1-alpine")
    #         logger.info(f"> Docker Ports:  5432: 1111")
    #         logger.info(f"> Docker POSTGRES_USER:  postgres")
    #         logger.info(f"> Docker POSTGRES_PASSWORD:  foo")
    #         logger.info(f"> Docker POSTGRES_DB:  testing_db")
    #         container = client.create_container(
    #             'postgis/postgis:12-3.1-alpine', ports=[1111, 5432], environment={"POSTGRES_USER": "postgres",
    #                                                                               "POSTGRES_PASSWORD": "foo1234",
    #                                                                               "PGUSER": "postgres",
    #                                                                               "POSTGRES_DB": "testing",
    #                                                                               "PGPORT": 5432},
    #             healthcheck={"test": ["CMD-SHELL", "pg_isready -U postgres"], "interval": 10000000000,
    #             "timeout": 5000000000,
    #                          "retries": 5},
    #             host_config=client.create_host_config(port_bindings={
    #                 5432: 1111,
    #             }), detach=True
    #         )
    #         container_id = container['Id']
    #         logger.info(f"> Docker container created with id: {container_id}")
    #         logger.info(f"> Starting Docker container with id: {container_id}")
    #         client.start(container_id)
    #         logger.info(f"> Docker container successfully started with id: {container_id}")
    #         testing_engine = create_engine("postgresql://postgres:foo@0.0.0.0:1111/testing_db", pool_pre_ping=True)
    #         testing_session = sessionmaker(autocommit=False, autoflush=False, bind=testing_engine)
    #         global_session.temp_session = global_session.SessionLocal
    #         global_session.SessionLocal = testing_session
    #         logger.info(f"> Docker container successfully removed with id: {container_id}")
    #     except Exception as err:
    #         logger.error("Error setting up testing database with docker.")
    try:
        alembic_runner.migrate_up_to("head")
    except exc.ProgrammingError:
        Base.metadata.drop_all(bind=engine)
    finally:
        alembic_runner.migrate_up_to("head")
    try:
        alembic_runner.migrate_down_to("base")
    except exc.ProgrammingError:
        Base.metadata.create_all(bind=engine)
    finally:
        Base.metadata.drop_all(bind=engine)
        alembic_runner.migrate_up_to("head")
    yield SessionLocal()
    # if container_id and client:
    #     client.remove_container(container_id, force=True)
    #


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://testserver") as c:
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


@pytest.fixture(scope="session")
def alembic_config() -> Config:
    alembic_config = Config(f"{script_location}/../../alembic.ini")
    alembic_config.set_main_option(
        "script_location", f"{script_location}/../../alembic"
    )
    return alembic_config


@pytest.fixture(scope="session")
def alembic_engine() -> Engine:
    """Override this fixture to provide pytest-alembic
    powered tests with a database handle."""
    # if settings.USE_CONTAINER_TESTING_DB:
    #     return sqlalchemy.create_engine(
    #         settings.SQLALCHEMY_DATABASE_TESTING_URI, pool_pre_ping=True
    #     )
    # else:
    return sqlalchemy.create_engine(
        settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True
    )


@pytest.fixture(scope="session")
def alembic_runner(alembic_config: Config, alembic_engine: Engine) -> MigrationContext:
    """Produce the primary alembic migration context in which to execute alembic tests.

    This fixture allows authoring custom tests which are specific to your particular
    migration history.
    """
    config = pytest_alembic.config.Config.from_raw_config(alembic_config)
    with pytest_alembic.runner(config=config, engine=alembic_engine) as runner:
        yield runner


@pytest.fixture(scope="function")
def random_sensor_1(db: Session) -> Generator[models.EnvirocarSensor, None, None]:
    sensor: models.EnvirocarSensor = create_random_sensor(db=db)
    yield sensor
    crud.sensor.remove(db=db, id=sensor.id)


@pytest.fixture(scope="function")
def random_track_1(db: Session) -> Generator[models.EnvirocarTrack, None, None]:
    sensor: models.EnvirocarSensor = create_random_sensor(db=db)
    track: models.EnvirocarTrack = create_random_track(db=db, sensor=sensor)
    yield track
    crud.track.remove(db=db, id=track.id)
    crud.sensor.remove(db=db, id=sensor.id)


@pytest.fixture(scope="function")
def random_track_measurement_1(
    db: Session,
) -> Generator[models.EnvirocarTrackMeasurement, None, None]:
    sensor: models.EnvirocarSensor = create_random_sensor(db=db)
    track: models.EnvirocarTrack = create_random_track(db=db, sensor=sensor)
    # TODO
    track_measurement: models.EnvirocarTrackMeasurement = create_random_track_measurement(
        db=db, track=track
    )
    yield track_measurement
    crud.track_measurement.remove(db=db, id=track.id)
    crud.track.remove(db=db, id=track.id)
    crud.sensor.remove(db=db, id=sensor.id)


@pytest.fixture(scope="function")
def mock_cfd_cars(db: Session) -> Generator[List[models.CarFuelDataCar], None, None]:
    db.query(models.CarFuelDataCar).delete()
    db.commit()
    cfd_reader_test: CarFuelDataReader = CarFuelDataReader(
        settings.CARFUELDATA_TEST_PATH_OR_URL
    )
    cfd_reader_test.fetch_and_process_data()
    BaseImporter(db=db).import_data(db_objects=cfd_reader_test.objects_list)

    yield cfd_reader_test.objects_list
    db.query(CarFuelDataCar).delete()
    db.commit()


@pytest.fixture(scope="function")
def envirocar_mocked_responses() -> Generator[responses.RequestsMock, None, None]:
    with responses.RequestsMock() as rsps:
        with open(settings.TEST_ENVIROCAR_PHENOMENONS_RESPONSE, mode="r") as f:
            phenomenons_response = json.load(f)
        with open(settings.TEST_ENVIROCAR_TRACKS_RESPONSE, mode="r") as f:
            tracks_response = json.load(f)
        with open(settings.TEST_ENVIROCAR_TRACK_MEASUREMENT_RESPONSE, mode="r") as f:
            track_measurement_response: Dict = json.load(f)
        with open(settings.TEST_ENVIROCAR_SENSORS_RESPONSE, mode="r") as f:
            sensors_response = json.load(f)
        rsps.add(
            method=responses.GET,
            url="https://test.com/phenomenons",
            json=phenomenons_response,
            status=200,
            content_type="application/json",
        )

        rsps.add(
            method=responses.GET,
            url="https://test.com/sensors",
            json=sensors_response,
            status=200,
            headers={
                "link": "<https://test.com/sensors/?limit=100&page=2>;rel=last;type=application/json"
            },
            content_type="application/json",
        )
        rsps.add(
            method=responses.GET,
            url="https://test.com/sensors/?limit=100&page=2",
            json=sensors_response,
            status=200,
            content_type="application/json",
        )

        rsps.add(
            method=responses.GET,
            url="https://test.com/tracks",
            json=tracks_response,
            status=200,
            headers={
                "link": "<https://test.com/tracks/?limit=10&page=2>;rel=last;type=application/json"
            },
            content_type="application/json",
        )
        rsps.add(
            method=responses.GET,
            url="https://test.com/tracks/?limit=10&page=2",
            json=tracks_response,
            status=200,
            content_type="application/json",
        )

        track_61d543bef4c3e97fbd56072d_measurements = track_measurement_response.get(
            "61d543bef4c3e97fbd56072d"
        )
        track_61d543bef4c3e97fbd560705_measurements = track_measurement_response.get(
            "61d543bef4c3e97fbd560705"
        )
        rsps.add(
            method=responses.GET,
            url="https://test.com/tracks/61d543bef4c3e97fbd56072d/measurements",
            json=track_61d543bef4c3e97fbd56072d_measurements,
            status=200,
            content_type="application/json",
        )
        rsps.add(
            method=responses.GET,
            url="https://test.com/tracks/61d543bef4c3e97fbd560705/measurements",
            json=track_61d543bef4c3e97fbd560705_measurements,
            status=200,
            content_type="application/json",
        )
        yield rsps
        rsps.reset()


@pytest.fixture(scope="function")
def mock_wikipedia_responses() -> Generator[responses.RequestsMock, None, None]:
    with responses.RequestsMock() as rsps:
        with open(
            settings.TEST_WIKIPEDIA_KATEGORIE_KLEINSTWAGEN_RESPONSE, mode="r"
        ) as f:
            kategorie_kleinstwagen_response = json.load(f)
        with open(
            settings.TEST_WIKIPEDIA_KATEGORIE_KLEINSTWAGEN_INFO_RESPONSE, mode="r"
        ) as f:
            kategorie_kleinstwagen_info_response = json.load(f)
        with open(
            settings.TEST_WIKIPEDIA_KATEGORIE_LEICHTFAHRZEUGE_RESPONSE, mode="r"
        ) as f:
            kategorie_leichtfahrzeuge_response = json.load(f)
        with open(
            settings.TEST_WIKIPEDIA_KATEGORIE_LEICHTFAHRZEUGE_INFO_RESPONSE, mode="r"
        ) as f:
            kategorie_leichtfahrzeuge_info_response = json.load(f)
        with open(settings.TEST_WIKIPEDIA_CATEGORY_MICROCARS_RESPONSE, mode="r") as f:
            kategorie_microcars_response = json.load(f)
        with open(
            settings.TEST_WIKIPEDIA_CATEGORY_MICROCARS_INFO_RESPONSE, mode="r"
        ) as f:
            kategorie_microcars_info_response = json.load(f)
        rsps.add(
            method=responses.GET,
            url="https://de.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Kategorie%3AKleinstwagen&cmlimit=500&format=json&redirects=1",  # noqa
            json=kategorie_kleinstwagen_response,
            status=200,
            content_type="application/json",
        )
        rsps.add(
            method=responses.GET,
            url="https://de.wikipedia.org/w/api.php?action=query&prop=info&titles=Kategorie%3AKleinstwagen&inprop=protection%7Ctalkid%7Cwatched%7Cwatchers%7Cvisitingwatchers%7Cnotificationtimestamp%7Csubjectid%7Curl%7Creadable%7Cpreload%7Cdisplaytitle&format=json&redirects=1",  # noqa
            json=kategorie_kleinstwagen_info_response,
            status=200,
            content_type="application/json",
        )
        rsps.add(
            method=responses.GET,
            url="https://de.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Kategorie%3ALeichtfahrzeug&cmlimit=500&format=json&redirects=1",  # noqa
            json=kategorie_leichtfahrzeuge_response,
            status=200,
            content_type="application/json",
        )
        rsps.add(
            method=responses.GET,
            url="https://de.wikipedia.org/w/api.php?action=query&prop=info&titles=Kategorie%3ALeichtfahrzeug&inprop=protection%7Ctalkid%7Cwatched%7Cwatchers%7Cvisitingwatchers%7Cnotificationtimestamp%7Csubjectid%7Curl%7Creadable%7Cpreload%7Cdisplaytitle&format=json&redirects=1",  # noqa
            json=kategorie_leichtfahrzeuge_info_response,
            status=200,
            content_type="application/json",
        )
        rsps.add(
            method=responses.GET,
            url="https://en.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category%3AMicrocars&cmlimit=500&format=json&redirects=1",  # noqa
            json=kategorie_microcars_response,
            status=200,
            content_type="application/json",
        )
        rsps.add(
            method=responses.GET,
            url="https://en.wikipedia.org/w/api.php?action=query&prop=info&titles=Category%3AMicrocars&inprop=protection%7Ctalkid%7Cwatched%7Cwatchers%7Cvisitingwatchers%7Cnotificationtimestamp%7Csubjectid%7Curl%7Creadable%7Cpreload%7Cdisplaytitle&format=json&redirects=1",  # noqa
            json=kategorie_microcars_info_response,
            status=200,
            content_type="application/json",
        )

        yield rsps
        rsps.reset()


@pytest.fixture(scope="function")
def mock_wikipedia_car_categories(
    db: Session, mock_wikipedia_responses: Generator[responses.RequestsMock, None, None]
) -> Generator[List[models.WikiCarCategory], None, None]:
    db.query(models.WikiCarCategory).delete()
    db.commit()
    test_car_category = {
        "car_categories": {
            "a": {
                "category_names": [
                    "Kategorie:Kleinstwagen",
                    "Kategorie:Leichtfahrzeug",
                    "Category:Microcars",
                ],
                "de": "Kleinstwagen",
                "en": "mini cars",
                "single_cars": [],
                "tank_capacity": 15,
            }
        }
    }
    wikipedia_reader: WikipediaReader = WikipediaReader(
        file_or_url=None, threads=None, categories=test_car_category
    )
    wikipedia_reader.fetch_and_process_data()
    BaseImporter(db=db).import_data(db_objects=wikipedia_reader.objects_ordered[0])
    yield wikipedia_reader.objects_ordered[0]
    db.query(WikiCarCategory).delete()
    db.commit()


@pytest.fixture(scope="function")
def json_download_mock() -> Generator[responses.RequestsMock, None, None]:
    with responses.RequestsMock() as rsps:
        with open(settings.TEST_ENVIROCAR_PHENOMENONS_RESPONSE, mode="r") as f:
            phenomenons_response = json.load(f)
        rsps.add(
            method=responses.GET,
            url="https://test.com/phenomenons.json",
            json=phenomenons_response,
            status=200,
            content_type="application/json",
        )
        yield rsps
        rsps.reset()