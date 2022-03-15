import json
import logging
import pathlib
from typing import AsyncGenerator, Dict, Generator, List, Tuple

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
from app import crud, schemas
from app.core.config import settings
from app.db.base_class import Base
from app.db.importer.base_importer import BaseImporter
from app.db.importer.carfueldata.carfueldata_reader import CarFuelDataReader
from app.db.importer.envirocar.envirocar_reader import EnvirocarReader
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
    create_mock_phenomenon_speed,
    create_random_sensor,
    create_random_sensor_statistic,
    create_random_track,
    create_random_track_measurement,
    create_sensors_by_cfd,
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
    config = pytest_alembic.config.Config.from_raw_config(alembic_config)
    with pytest_alembic.runner(config=config, engine=alembic_engine) as runner:
        yield runner


@pytest.fixture(scope="session")
def random_sensor_gasoline_1(db: Session) -> Generator[EnvirocarSensor, None, None]:
    sensor: EnvirocarSensor = create_random_sensor(
        db=db, unique_id=654321, fueltype="gasoline"
    )
    yield sensor
    crud.envirocar_sensor.remove(db=db, id=sensor.id)


@pytest.fixture(scope="session")
def random_sensor_gasoline_2(db: Session) -> Generator[EnvirocarSensor, None, None]:
    sensor: EnvirocarSensor = create_random_sensor(
        db=db, unique_id=1234567, fueltype="gasoline"
    )
    yield sensor
    crud.envirocar_sensor.remove(db=db, id=sensor.id)


@pytest.fixture(scope="session")
def random_sensor_diesel_1(db: Session) -> Generator[EnvirocarSensor, None, None]:
    sensor: EnvirocarSensor = create_random_sensor(
        db=db, unique_id=6666666, fueltype="diesel"
    )
    yield sensor
    crud.envirocar_sensor.remove(db=db, id=sensor.id)


@pytest.fixture(scope="session")
def random_track_1(db: Session) -> Generator[EnvirocarTrack, None, None]:
    sensor: EnvirocarSensor = create_random_sensor(db=db)
    track: EnvirocarTrack = create_random_track(db=db, sensor=sensor)
    yield track
    crud.envirocar_track.remove(db=db, id=track.id)
    crud.envirocar_sensor.remove(db=db, id=sensor.id)


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
def mock_cfd_cars(db: Session) -> Generator[List[CarFuelDataCar], None, None]:
    cfd_reader_test: CarFuelDataReader = CarFuelDataReader(
        settings.CARFUELDATA_TEST_PATH_OR_URL
    )
    cfd_reader_test.fetch_and_process_data()
    BaseImporter(db=db).import_data(db_objects=cfd_reader_test.objects_list)

    yield cfd_reader_test.objects_list

    for db_object in cfd_reader_test.objects_list:
        if db_object.id is None:
            continue
        db.delete(db_object)
    db.commit()


@pytest.fixture(scope="module")
def mock_wikipedia_objects(
    db: Session, mock_all_responses: Generator[responses.RequestsMock, None, None]
) -> Generator[Tuple[List[WikiCarCategory], List[WikiCar]], None, None]:
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
    for index, db_objects in wikipedia_reader.objects_ordered.items():
        BaseImporter(db=db).import_data(db_objects=db_objects)
    yield wikipedia_reader.objects_ordered[0], wikipedia_reader.objects_ordered[1]

    wikicar: WikiCar
    for wikicar in wikipedia_reader.objects_ordered[1]:
        db.delete(wikicar)
    db.commit()
    wikicar_category: WikiCarCategory
    for wikicar_category in wikipedia_reader.objects_ordered[0]:
        db.delete(wikicar_category)
    db.commit()


@pytest.fixture(scope="function")
def mock_all_matched_fast(
    db: Session, mock_cfd_cars: Generator[List[CarFuelDataCar], None, None]
) -> Generator[
    Tuple[List[EnvirocarSensor], Generator[List[CarFuelDataCar], None, None]],
    None,
    None,
]:
    db.query(EnvirocarSensor).delete()
    db.commit()

    mock_cfd_car: CarFuelDataCar
    envirocar_sensors: List[EnvirocarSensor] = create_sensors_by_cfd(db=db, cfd_cars=mock_cfd_cars)  # type: ignore
    # TODO wikicarenvirocar matches hier erstellen. maybe just take the two mock sensors with driving stats.
    yield envirocar_sensors, mock_cfd_cars

    for db_object in envirocar_sensors:
        db.delete(db_object)
    db.commit()


@pytest.fixture(scope="module")
def mock_all_envirocar_sensors(
    db: Session,
    mock_wikipedia_objects: Tuple[List[WikiCarCategory], List[WikiCar]],
    mock_all_responses: responses.RequestsMock,
) -> Generator[Dict, None, None]:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        file_or_url=None,
        envirocar_base_url="https://envirocar.org/api/stable",
        threads=None,
        db=db,
    )
    envirocar_reader.fetch_and_process_data()
    # Import the data
    for index, db_objects in envirocar_reader.objects_ordered.items():
        BaseImporter(db=db).import_data(db_objects=db_objects)
    yield envirocar_reader.objects_ordered
    for index, db_objects in reversed(envirocar_reader.objects_ordered.items()):
        for db_object in db_objects:
            db.delete(db_object)
        db.commit()


@pytest.fixture(scope="session")
def mock_envirocar_speed_phenomenon(
    db: Session,
) -> Generator[EnvirocarPhenomenon, None, None]:
    speed_mock: EnvirocarPhenomenon = create_mock_phenomenon_speed(db=db)
    yield speed_mock
    crud.envirocar_phenomenon.remove(db=db, id=speed_mock.id)


@pytest.fixture(scope="session")
def mock_envirocar_co2_phenomenon(
    db: Session,
) -> Generator[EnvirocarPhenomenon, None, None]:
    co2_mock: EnvirocarPhenomenon = create_mock_phenomenon_co2(db=db)
    yield co2_mock
    crud.envirocar_phenomenon.remove(db=db, id=co2_mock.id)


@pytest.fixture(scope="session")
def mock_envirocar_consumption_phenomenon(
    db: Session,
) -> Generator[EnvirocarPhenomenon, None, None]:
    consumption_mock: EnvirocarPhenomenon = create_mock_phenomenon_consumption(db=db)
    yield consumption_mock
    crud.envirocar_phenomenon.remove(db=db, id=consumption_mock.id)


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
def mock_sensor_statistics_gasoline_consumption_2(
    db: Session,
    random_sensor_gasoline_2: EnvirocarSensor,
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


@pytest.fixture(scope="session")
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
