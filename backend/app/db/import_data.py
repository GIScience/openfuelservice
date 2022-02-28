import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import base  # noqa: F401
from app.db.importer.base_importer import BaseImporter
from app.db.importer.carfueldata.carfueldata_reader import CarFuelDataReader
from app.db.importer.countries.countries_reader import CountryCodesReader
from app.db.importer.envirocar.envirocar_reader import EnvirocarReader
from app.db.importer.fuelprices.eurostat_reader import EurostatFuelReader
from app.db.importer.wikipedia.wikipedia_reader import WikipediaReader

logger = logging.getLogger(__name__)


def import_all_data(db: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line
    # Base.metadata.create_all(bind=engine)

    # Import Countries
    country_codes_reader: CountryCodesReader = CountryCodesReader(
        settings.COUNTRY_CODES_TEST_PATH
    )
    country_codes_reader.fetch_and_process_data()
    country_codes_reader.enrich_with_geometries(settings.COUNTRY_BOUNDARIES_TEST_PATH)
    BaseImporter(db=db).import_data(db_objects=country_codes_reader.objects_list)

    # Import Fuel Data
    eurostat_reader = EurostatFuelReader(
        settings.EUROSTAT_TEST_FUEL_HISTORY_2005_ONWARDS, db=db
    )
    eurostat_reader.fetch_and_process_data()
    BaseImporter(db=db).import_data(db_objects=eurostat_reader.objects_list)

    # Import Wikipedia Data
    wikipedia_reader: WikipediaReader = WikipediaReader(
        file_or_url=None, threads=None, categories=settings.CAR_CATEGORIES
    )
    wikipedia_reader.fetch_and_process_data()
    for index, object_collection in wikipedia_reader.objects_ordered.items():
        BaseImporter(db=db).import_data(db_objects=object_collection)

    # Import CarFuelData
    cfd_reader_test: CarFuelDataReader = CarFuelDataReader(
        settings.CARFUELDATA_TEST_PATH_OR_URL
    )
    cfd_reader_test.fetch_and_process_data()
    BaseImporter(db=db).import_data(db_objects=cfd_reader_test.objects_list)

    # Import and Match Envirocar Data
    envirocar_reader: EnvirocarReader = EnvirocarReader(db=db)
    envirocar_reader.fetch_and_process_data()

    for index, object_collection in envirocar_reader.objects_ordered.items():
        BaseImporter(db=db).import_data(db_objects=object_collection)
