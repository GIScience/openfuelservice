import asyncio
import json
import logging
import pathlib
import random
from asyncio import AbstractEventLoop
from typing import AsyncGenerator, Dict, Generator, List, Tuple

import pytest
import pytest_alembic
import pytest_asyncio
import responses
import sqlalchemy
from fastapi.testclient import TestClient
from httpx import AsyncClient
from pytest_alembic.runner import MigrationContext
from sqlalchemy import exc, inspect
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session

from alembic.config import Config
from app import crud, schemas
from app.core.config import settings
from app.db.base_class import Base
from app.db.importer.carfueldata.carfueldata_reader import CarFuelDataReader
from app.db.importer.wikipedia.wikipedia_reader import WikipediaReader
from app.db.session import SessionLocal, engine
from app.main import app
from app.models import (
    CarFuelDataCar,
    EnvirocarPhenomenon,
    EnvirocarSensor,
    EnvirocarSensorStatistic,
    EnvirocarTrack,
    EnvirocarTrackMeasurement,
    WikiCar,
    WikiCarCategory,
)
from app.tests.utils.envirocar import (
    create_mock_phenomenon_co2,
    create_mock_phenomenon_consumption,
    create_mock_phenomenon_engine_load,
    create_mock_phenomenon_speed,
    create_random_sensor,
    create_random_sensor_statistic,
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
        Base.metadata.drop_all(bind=engine)  # type: ignore
    finally:
        alembic_runner.migrate_up_to("head")
    try:
        alembic_runner.migrate_down_to("base")
    except exc.ProgrammingError:
        Base.metadata.create_all(bind=engine)  # type: ignore
    finally:
        Base.metadata.drop_all(bind=engine)  # type: ignore
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
def event_loop() -> AbstractEventLoop:
    # Fixes a bug in asyncio. For details see:
    # https://stackoverflow.com/questions/63713575/pytest-issues-with-a-session-scoped-fixture-and-asyncio
    return asyncio.get_event_loop()


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
def alembic_runner(
    alembic_config: Config, alembic_engine: Engine
) -> Generator[MigrationContext, None, None]:
    """Produce the primary alembic migration context in which to execute alembic tests.

    This fixture allows authoring custom tests which are specific to your particular
    migration history.
    """
    config = pytest_alembic.config.Config.from_raw_config(alembic_config)  # type: ignore
    with pytest_alembic.runner(config=config, engine=alembic_engine) as runner:
        yield runner


@pytest.fixture(scope="class")
def random_sensor_gasoline_1(db: Session) -> Generator[EnvirocarSensor, None, None]:
    sensor: EnvirocarSensor = create_random_sensor(
        db=db, unique_id=654321, fueltype="gasoline"
    )
    yield sensor
    crud.envirocar_sensor.remove(db=db, id=sensor.id)


@pytest.fixture(scope="class")
def random_sensor_gasoline_2(db: Session) -> Generator[EnvirocarSensor, None, None]:
    sensor: EnvirocarSensor = create_random_sensor(
        db=db, unique_id=1234567, fueltype="gasoline"
    )
    yield sensor
    crud.envirocar_sensor.remove(db=db, id=sensor.id)


@pytest.fixture(scope="class")
def random_sensor_diesel_1(db: Session) -> Generator[EnvirocarSensor, None, None]:
    sensor: EnvirocarSensor = create_random_sensor(
        db=db, unique_id=6666666, fueltype="diesel"
    )
    yield sensor
    crud.envirocar_sensor.remove(db=db, id=sensor.id)


@pytest.fixture(scope="class")
def random_track_1(db: Session) -> Generator[EnvirocarTrack, None, None]:
    sensor: EnvirocarSensor = create_random_sensor(db=db)
    track: EnvirocarTrack = create_random_track(db=db, sensor=sensor)
    yield track
    crud.envirocar_track.remove(db=db, id=track.id)
    crud.envirocar_sensor.remove(db=db, id=sensor.id)


@pytest.fixture(scope="class")
def random_track_measurement_1(
    db: Session,
) -> Generator[EnvirocarTrackMeasurement, None, None]:
    sensor: EnvirocarSensor = create_random_sensor(db=db)
    track: EnvirocarTrack = create_random_track(db=db, sensor=sensor)
    # TODO
    track_measurement: EnvirocarTrackMeasurement = create_random_track_measurement(
        db=db, track=track
    )
    yield track_measurement
    crud.envirocar_track_measurement.remove(db=db, id=track.id)
    crud.envirocar_track.remove(db=db, id=track.id)
    crud.envirocar_sensor.remove(db=db, id=sensor.id)


@pytest.fixture(scope="session", autouse=True)
def mock_all_responses() -> Generator[responses.RequestsMock, None, None]:
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
        with open(settings.TEST_ENVIROCAR_PHENOMENONS_RESPONSE, mode="r") as f:
            phenomenons_response = json.load(f)
        with open(settings.TEST_ENVIROCAR_TRACKS_RESPONSE, mode="r") as f:
            tracks_response = json.load(f)
        with open(settings.TEST_ENVIROCAR_TRACK_MEASUREMENT_RESPONSE, mode="r") as f:
            track_measurement_response: Dict = json.load(f)
        with open(settings.TEST_ENVIROCAR_SENSORS_RESPONSE, mode="r") as f:
            sensors_response = json.load(f)
        with open(settings.TEST_ENVIROCAR_SENSORS_STATISTICS_RESPONSE, mode="r") as f:
            sensors_statistics_response = json.load(f)

        rsps.add(
            method=responses.GET,
            url="https://de.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Kategorie%3AKleinst"
            "wagen&cmlimit=500&format=json&redirects=1",
            json=kategorie_kleinstwagen_response,
            status=200,
            content_type="application/json",
        )
        rsps.add(
            method=responses.GET,
            url="https://de.wikipedia.org/w/api.php?action=query&prop=info&titles=Kategorie%3AKleinstwagen&inprop="
            "protection%7Ctalkid%7Cwatched%7Cwatchers%7Cvisitingwatchers%7Cnotificationtimestamp%7Csubjectid%7"
            "Curl%7Creadable%7Cpreload%7Cdisplaytitle&format=json&redirects=1",
            json=kategorie_kleinstwagen_info_response,
            status=200,
            content_type="application/json",
        )
        rsps.add(
            method=responses.GET,
            url="https://de.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Kategorie%3A"
            "Leichtfahrzeug&cmlimit=500&format=json&redirects=1",
            json=kategorie_leichtfahrzeuge_response,
            status=200,
            content_type="application/json",
        )
        rsps.add(
            method=responses.GET,
            url="https://de.wikipedia.org/w/api.php?action=query&prop=info&titles=Kategorie%3ALeichtfahrzeug&inprop"
            "=protection%7Ctalkid%7Cwatched%7Cwatchers%7Cvisitingwatchers%7Cnotificationtimestamp%7Csubjectid%"
            "7Curl%7Creadable%7Cpreload%7Cdisplaytitle&format=json&redirects=1",
            json=kategorie_leichtfahrzeuge_info_response,
            status=200,
            content_type="application/json",
        )
        rsps.add(
            method=responses.GET,
            url="https://en.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category%3AMicrocars"
            "&cmlimit=500&format=json&redirects=1",
            json=kategorie_microcars_response,
            status=200,
            content_type="application/json",
        )
        rsps.add(
            method=responses.GET,
            url="https://en.wikipedia.org/w/api.php?action=query&prop=info&titles=Category%3AMicrocars&inprop="
            "protection%7Ctalkid%7Cwatched%7Cwatchers%7Cvisitingwatchers%7Cnotificationtimestamp%7Csubjectid%7Curl"
            "%7Creadable%7Cpreload%7Cdisplaytitle&format=json&redirects=1",
            json=kategorie_microcars_info_response,
            status=200,
            content_type="application/json",
        )
        rsps.add(
            method=responses.GET,
            url="https://envirocar.org/api/stable/phenomenons",
            json=phenomenons_response,
            status=200,
            content_type="application/json",
        )

        rsps.add(
            method=responses.GET,
            url="https://envirocar.org/api/stable/sensors",
            json=sensors_response,
            status=200,
            headers={
                "link": "<https://envirocar.org/api/stable/sensors/?limit=100&page=2>;rel=last;type=application/json"
            },
            content_type="application/json",
        )
        rsps.add(
            method=responses.GET,
            url="https://envirocar.org/api/stable/sensors/?limit=100&page=2",
            json=sensors_response,
            status=200,
            content_type="application/json",
        )

        sensor_statistics_5fd9d14e05fa792e88dc8b7b = sensors_statistics_response.get(
            "5fd9d14e05fa792e88dc8b7b"
        )
        sensor_statistics_616010fb0bd6756ea3a9aea7 = sensors_statistics_response.get(
            "616010fb0bd6756ea3a9aea7"
        )
        sensor_statistics_574e78cbe4b09078f97bbb4a = sensors_statistics_response.get(
            "574e78cbe4b09078f97bbb4a"
        )

        rsps.add(
            method=responses.GET,
            url="https://envirocar.org/api/stable/sensors/5fd9d14e05fa792e88dc8b7b/statistics",
            json=sensor_statistics_5fd9d14e05fa792e88dc8b7b,
            status=200,
            content_type="application/json",
        )

        rsps.add(
            method=responses.GET,
            url="https://envirocar.org/api/stable/sensors/616010fb0bd6756ea3a9aea7/statistics",
            json=sensor_statistics_616010fb0bd6756ea3a9aea7,
            status=200,
            content_type="application/json",
        )

        rsps.add(
            method=responses.GET,
            url="https://envirocar.org/api/stable/sensors/574e78cbe4b09078f97bbb4a/statistics",
            json=sensor_statistics_574e78cbe4b09078f97bbb4a,
            status=200,
            content_type="application/json",
        )

        rsps.add(
            method=responses.GET,
            url="https://envirocar.org/api/stable/tracks",
            json=tracks_response,
            status=200,
            headers={
                "link": "<https://envirocar.org/api/stable/tracks/?limit=10&page=2>;rel=last;type=application/json"
            },
            content_type="application/json",
        )
        rsps.add(
            method=responses.GET,
            url="https://envirocar.org/api/stable/tracks/?limit=10&page=2",
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
            url="https://envirocar.org/api/stable/tracks/61d543bef4c3e97fbd56072d/measurements",
            json=track_61d543bef4c3e97fbd56072d_measurements,
            status=200,
            content_type="application/json",
        )
        rsps.add(
            method=responses.GET,
            url="https://envirocar.org/api/stable/tracks/61d543bef4c3e97fbd560705/measurements",
            json=track_61d543bef4c3e97fbd560705_measurements,
            status=200,
            content_type="application/json",
        )
        yield rsps
        rsps.reset()


@pytest_asyncio.fixture(scope="session")
async def mock_cfd_cars(db: Session) -> AsyncGenerator[List[CarFuelDataCar], None]:
    cfd_reader_test: CarFuelDataReader = CarFuelDataReader(
        db=db, file_to_read=settings.CARFUELDATA_TEST_PATH_OR_URL
    )
    await cfd_reader_test.fetch_process_and_import_data(import_data=True)
    yield cfd_reader_test.objects_list

    for db_object in cfd_reader_test.objects_list:
        if db_object.id is None:
            continue
        db.delete(db_object)
    db.commit()


@pytest_asyncio.fixture(scope="session")
async def mock_wikipedia_objects(
    db: Session, mock_all_responses: Generator[responses.RequestsMock, None, None]
) -> AsyncGenerator[Tuple[List[WikiCarCategory], List[WikiCar]], None]:
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
        db=db, file_or_url=None, threads=None, categories=test_car_category
    )
    await wikipedia_reader.fetch_process_and_import_data(import_data=True)
    yield wikipedia_reader.categories, wikipedia_reader.wiki_cars

    db.commit()
    wikicar: WikiCar
    for wikicar in wikipedia_reader.wiki_cars:
        insp = inspect(wikicar)
        if not insp.expired and wikicar.id is not None:
            db.delete(wikicar)
        else:
            pass
    db.commit()
    wikicar_category: WikiCarCategory
    for wikicar_category in wikipedia_reader.categories:
        insp = inspect(wikicar_category)
        if not insp.expired and wikicar_category.id is not None:
            db.delete(wikicar_category)
        else:
            pass
    db.commit()


@pytest.fixture(scope="class")
def mock_envirocar_speed_phenomenon(
    db: Session,
) -> Generator[EnvirocarPhenomenon, None, None]:
    speed_mock: EnvirocarPhenomenon = create_mock_phenomenon_speed(db=db)
    yield speed_mock
    crud.envirocar_phenomenon.remove(db=db, id=speed_mock.id)


@pytest.fixture(scope="class")
def mock_envirocar_co2_phenomenon(
    db: Session,
) -> Generator[EnvirocarPhenomenon, None, None]:
    co2_mock: EnvirocarPhenomenon = create_mock_phenomenon_co2(db=db)
    yield co2_mock
    crud.envirocar_phenomenon.remove(db=db, id=co2_mock.id)


@pytest.fixture(scope="class")
def mock_envirocar_consumption_phenomenon(
    db: Session,
) -> Generator[EnvirocarPhenomenon, None, None]:
    consumption_mock: EnvirocarPhenomenon = create_mock_phenomenon_consumption(db=db)
    yield consumption_mock
    crud.envirocar_phenomenon.remove(db=db, id=consumption_mock.id)


@pytest.fixture(scope="class")
def mock_envirocar_engine_load_phenomenon(
    db: Session,
) -> Generator[EnvirocarPhenomenon, None, None]:
    engine_load_mock: EnvirocarPhenomenon = create_mock_phenomenon_engine_load(db=db)
    yield engine_load_mock
    crud.envirocar_phenomenon.remove(db=db, id=engine_load_mock.id)


@pytest.fixture(scope="class")
def mock_sensor_statistics_gasoline_co2_1(
    db: Session,
    random_sensor_gasoline_1: EnvirocarSensor,
    mock_envirocar_co2_phenomenon: EnvirocarPhenomenon,
) -> Generator[EnvirocarSensorStatistic, None, None]:
    statistic_mock: EnvirocarSensorStatistic = create_random_sensor_statistic(
        db=db, sensor=random_sensor_gasoline_1, phenomenon=mock_envirocar_co2_phenomenon
    )
    yield statistic_mock
    crud.envirocar_sensor_statistic.remove(
        db=db, id=(statistic_mock.id, statistic_mock.name)
    )


@pytest.fixture(scope="class")
def mock_sensor_statistics_gasoline_co2_2(
    db: Session,
    random_sensor_gasoline_2: EnvirocarSensor,
    mock_envirocar_co2_phenomenon: EnvirocarPhenomenon,
) -> Generator[EnvirocarSensorStatistic, None, None]:
    statistic_mock: EnvirocarSensorStatistic = create_random_sensor_statistic(
        db=db, sensor=random_sensor_gasoline_2, phenomenon=mock_envirocar_co2_phenomenon
    )
    yield statistic_mock
    crud.envirocar_sensor_statistic.remove(
        db=db, id=(statistic_mock.id, statistic_mock.name)
    )


@pytest.fixture(scope="class")
def mock_sensor_statistics_diesel_co2_1(
    db: Session,
    random_sensor_diesel_1: EnvirocarSensor,
    mock_envirocar_co2_phenomenon: EnvirocarPhenomenon,
) -> Generator[EnvirocarSensorStatistic, None, None]:
    statistic_mock: EnvirocarSensorStatistic = create_random_sensor_statistic(
        db=db, sensor=random_sensor_diesel_1, phenomenon=mock_envirocar_co2_phenomenon
    )
    yield statistic_mock
    crud.envirocar_sensor_statistic.remove(
        db=db, id=(statistic_mock.id, statistic_mock.name)
    )


@pytest.fixture(scope="class")
def mock_sensor_statistics_gasoline_speed_1(
    db: Session,
    random_sensor_gasoline_1: EnvirocarSensor,
    mock_envirocar_speed_phenomenon: EnvirocarPhenomenon,
) -> Generator[EnvirocarSensorStatistic, None, None]:
    statistic_mock: EnvirocarSensorStatistic = create_random_sensor_statistic(
        db=db,
        sensor=random_sensor_gasoline_1,
        phenomenon=mock_envirocar_speed_phenomenon,
    )
    yield statistic_mock
    crud.envirocar_sensor_statistic.remove(
        db=db, id=(statistic_mock.id, statistic_mock.name)
    )


@pytest.fixture(scope="class")
def mock_sensor_statistics_gasoline_speed_2(
    db: Session,
    random_sensor_gasoline_2: EnvirocarSensor,
    mock_envirocar_speed_phenomenon: EnvirocarPhenomenon,
) -> Generator[EnvirocarSensorStatistic, None, None]:
    statistic_mock: EnvirocarSensorStatistic = create_random_sensor_statistic(
        db=db,
        sensor=random_sensor_gasoline_2,
        phenomenon=mock_envirocar_speed_phenomenon,
    )
    yield statistic_mock
    crud.envirocar_sensor_statistic.remove(
        db=db, id=(statistic_mock.id, statistic_mock.name)
    )


@pytest.fixture(scope="class")
def mock_sensor_statistics_diesel_speed_1(
    db: Session,
    random_sensor_diesel_1: EnvirocarSensor,
    mock_envirocar_speed_phenomenon: EnvirocarPhenomenon,
) -> Generator[EnvirocarSensorStatistic, None, None]:
    statistic_mock: EnvirocarSensorStatistic = create_random_sensor_statistic(
        db=db, sensor=random_sensor_diesel_1, phenomenon=mock_envirocar_speed_phenomenon
    )
    yield statistic_mock
    crud.envirocar_sensor_statistic.remove(
        db=db, id=(statistic_mock.id, statistic_mock.name)
    )


@pytest.fixture(scope="class")
def mock_sensor_statistics_gasoline_consumption_1(
    db: Session,
    random_sensor_gasoline_1: EnvirocarSensor,
    mock_envirocar_consumption_phenomenon: EnvirocarPhenomenon,
) -> Generator[EnvirocarSensorStatistic, None, None]:
    statistic_mock: EnvirocarSensorStatistic = create_random_sensor_statistic(
        db=db,
        sensor=random_sensor_gasoline_1,
        phenomenon=mock_envirocar_consumption_phenomenon,
    )
    yield statistic_mock
    crud.envirocar_sensor_statistic.remove(
        db=db, id=(statistic_mock.id, statistic_mock.name)
    )


@pytest.fixture(scope="class")
def mock_sensor_statistics_gasoline_consumption_2(
    db: Session,
    random_sensor_gasoline_2: EnvirocarSensor,  #
    mock_envirocar_consumption_phenomenon: EnvirocarPhenomenon,
) -> Generator[EnvirocarSensorStatistic, None, None]:
    statistic_mock: EnvirocarSensorStatistic = create_random_sensor_statistic(
        db=db,
        sensor=random_sensor_gasoline_2,
        phenomenon=mock_envirocar_consumption_phenomenon,
    )
    yield statistic_mock
    crud.envirocar_sensor_statistic.remove(
        db=db, id=(statistic_mock.id, statistic_mock.name)
    )


@pytest.fixture(scope="class")
def mock_sensor_statistics_diesel_consumption_1(
    db: Session,
    random_sensor_diesel_1: EnvirocarSensor,
    mock_envirocar_consumption_phenomenon: EnvirocarPhenomenon,
) -> Generator[EnvirocarSensorStatistic, None, None]:
    statistic_mock: EnvirocarSensorStatistic = create_random_sensor_statistic(
        db=db,
        sensor=random_sensor_diesel_1,
        phenomenon=mock_envirocar_consumption_phenomenon,
    )
    yield statistic_mock
    crud.envirocar_sensor_statistic.remove(
        db=db, id=(statistic_mock.id, statistic_mock.name)
    )


@pytest.fixture(scope="class")
def mock_envirocar_sensors_with_statistics_only(
    db: Session,
    mock_envirocar_speed_phenomenon: EnvirocarPhenomenon,
    mock_envirocar_co2_phenomenon: EnvirocarPhenomenon,
    mock_envirocar_consumption_phenomenon: EnvirocarPhenomenon,
    mock_envirocar_engine_load_phenomenon: EnvirocarPhenomenon,
) -> Generator[List[EnvirocarSensor], None, None]:
    sensors: List[EnvirocarSensor] = []
    statistics: List[EnvirocarSensorStatistic] = []

    sensor1 = create_random_sensor(
        db=db,
        unique_id=random.randint(0, 999999),
        sensor_type="car",
        sensor_model="Golf V Plus 1.6",
        manufacturer="VW",
        fueltype="gasoline",
        constructionyear=2006,
        enginedisplacement=1595,
    )

    sensor2 = create_random_sensor(
        db=db,
        unique_id=random.randint(0, 999999),
        sensor_type="car",
        sensor_model="Corsa",
        manufacturer="OPEL",
        fueltype="diesel",
        constructionyear=2009,
        enginedisplacement=1398,
    )
    sensor3 = create_random_sensor(
        db=db,
        unique_id=random.randint(0, 999999),
        sensor_type="car",
        sensor_model="Avensis",
        manufacturer="Toyota",
        fueltype="gasoline",
        constructionyear=2011,
        enginedisplacement=1800,
    )
    sensors.extend([sensor1, sensor2, sensor3])

    sensor1_engine_load = create_random_sensor_statistic(
        db=db,
        sensor=sensor1,
        phenomenon=mock_envirocar_engine_load_phenomenon,
        max=49.8039222301221116140368394553661346435546875,
        avg=33.3038501649215987754359957762062549591064453125,
        min=0,
        measurements=30181,
        tracks=184,
        sensors=1,
        users=2,
    )
    sensor1_speed = create_random_sensor_statistic(
        db=db,
        sensor=sensor1,
        phenomenon=mock_envirocar_speed_phenomenon,
        max=161,
        avg=67.639957590996147018813644535839557647705078125,
        min=0,
        measurements=30183,
        tracks=184,
        sensors=1,
        users=2,
    )
    sensor1_consumption = create_random_sensor_statistic(
        db=db,
        sensor=sensor1,
        phenomenon=mock_envirocar_consumption_phenomenon,
        max=17.104029273399309118985911482013761997222900390625,
        avg=4.37194840215625912804853214765898883342742919921875,
        min=0,
        measurements=30171,
        tracks=184,
        sensors=1,
        users=2,
    )
    sensor1_co2 = create_random_sensor_statistic(
        db=db,
        sensor=sensor1,
        phenomenon=mock_envirocar_co2_phenomenon,
        max=40.194468792488379449423518963158130645751953125,
        avg=10.2740787450670865155188948847353458404541015625,
        min=0,
        measurements=30171,
        tracks=184,
        sensors=1,
        users=2,
    )
    statistics.extend(
        [sensor1_engine_load, sensor1_speed, sensor1_consumption, sensor1_co2]
    )
    sensor2_engine_load = create_random_sensor_statistic(
        db=db,
        sensor=sensor2,
        phenomenon=mock_envirocar_engine_load_phenomenon,
        max=73.71183985681335570916417054831981658935546875,
        avg=14.8596056754359597817938265507109463214874267578125,
        min=0,
        measurements=556,
        tracks=3,
        sensors=1,
        users=1,
    )
    sensor2_speed = create_random_sensor_statistic(
        db=db,
        sensor=sensor2,
        phenomenon=mock_envirocar_speed_phenomenon,
        max=255.0000075995922088623046875,
        avg=30.254225126296372394563150010071694850921630859375,
        min=0,
        measurements=556,
        tracks=3,
        sensors=1,
        users=1,
    )
    sensor2_consumption = create_random_sensor_statistic(
        db=db,
        sensor=sensor2,
        phenomenon=mock_envirocar_consumption_phenomenon,
        max=18.3919219078163536096326424740254878997802734375,
        avg=2.11468071096669429920211769058369100093841552734375,
        min=0,
        measurements=556,
        tracks=3,
        sensors=1,
        users=1,
    )
    sensor2_co2 = create_random_sensor_statistic(
        db=db,
        sensor=sensor2,
        phenomenon=mock_envirocar_co2_phenomenon,
        max=43.221016483368430272093974053859710693359375,
        avg=4.96949967077173138108037164784036576747894287109375,
        min=0,
        measurements=556,
        tracks=3,
        sensors=1,
        users=1,
    )
    statistics.extend(
        [sensor2_engine_load, sensor2_speed, sensor2_consumption, sensor2_co2]
    )

    sensor3_engine_load = create_random_sensor_statistic(
        db=db,
        sensor=sensor3,
        phenomenon=mock_envirocar_engine_load_phenomenon,
        max=100.00000298023223876953125,
        avg=63.98008355519086620688540278933942317962646484375,
        min=0,
        measurements=359162,
        tracks=1476,
        sensors=1,
        users=1,
    )
    sensor3_speed = create_random_sensor_statistic(
        db=db,
        sensor=sensor3,
        phenomenon=mock_envirocar_speed_phenomenon,
        max=172.99999516643583774566650390625,
        avg=66.621938327232186338733299635350704193115234375,
        min=0,
        measurements=359162,
        tracks=1476,
        sensors=1,
        users=1,
    )
    sensor3_consumption = create_random_sensor_statistic(
        db=db,
        sensor=sensor3,
        phenomenon=mock_envirocar_consumption_phenomenon,
        max=25.797251971912313450729925534687936305999755859375,
        avg=4.58364373856346762892144397483207285404205322265625,
        min=0.409195294962839961616651862641447223722934722900390625,
        measurements=359162,
        tracks=1476,
        sensors=1,
        users=1,
    )
    sensor3_co2 = create_random_sensor_statistic(
        db=db,
        sensor=sensor3,
        phenomenon=mock_envirocar_co2_phenomenon,
        max=60.623542133993936431579641066491603851318359375,
        avg=10.77156278562436142465230659581720829010009765625,
        min=0.9616089431626739791880709162796847522258758544921875,
        measurements=359162,
        tracks=1476,
        sensors=1,
        users=1,
    )
    statistics.extend(
        [sensor3_engine_load, sensor3_speed, sensor3_consumption, sensor3_co2]
    )

    yield [sensor1, sensor2, sensor3]

    for statistics_db_object in statistics:
        db.delete(statistics_db_object)
    db.commit()
    for sensor_db_object in sensors:
        db.delete(sensor_db_object)
    db.commit()


@pytest.fixture(scope="function")
def json_download_mock() -> Generator[responses.RequestsMock, None, None]:
    with responses.RequestsMock() as rsps:
        with open(settings.TEST_ENVIROCAR_PHENOMENONS_RESPONSE, mode="r") as f:
            phenomenons_response = json.load(f)
        rsps.add(
            method=responses.GET,
            url="https://envirocar.org/api/stable/phenomenons.json",
            json=phenomenons_response,
            status=200,
            content_type="application/json",
        )
        yield rsps
        rsps.reset()


@pytest.fixture(scope="session")
def openrouteservice_example_response() -> Generator[Dict, None, None]:
    with open(
        settings.OPENROUTESERVICE_EXAMPLE_REQUEST_HEIDELBERG, encoding="utf-8"
    ) as f:
        geometry = json.load(f)
    yield geometry
