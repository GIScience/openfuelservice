import asyncio
import logging
from asyncio import Event
from typing import List

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import base  # noqa: F401
from app.db.importer.carfueldata.carfueldata_reader import CarFuelDataReader
from app.db.importer.countries.countries_reader import CountryCodesReader
from app.db.importer.envirocar.envirocar_reader import EnvirocarReader
from app.db.importer.fuelprices.eurostat_reader import EurostatFuelReader
from app.db.importer.wikipedia.wikipedia_reader import WikipediaReader

logger = logging.getLogger(__name__)


async def import_all_data(db: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line
    # Base.metadata.create_all(bind=engine)
    asyncio.get_event_loop()
    tasks: List = []
    # Import Countries
    country_codes_reader: CountryCodesReader = CountryCodesReader(
        db=db,
        file_to_read=settings.COUNTRY_CODES_TEST_PATH,
        country_geometry_file=settings.COUNTRY_BOUNDARIES_TEST_PATH,
    )
    country_codes_reader_event: Event = asyncio.Event()
    tasks.append(
        asyncio.create_task(
            country_codes_reader.fetch_process_and_import_data(
                import_data=True, event_to_set=country_codes_reader_event
            )
        )
    )

    # Import Wikipedia Data
    wikipedia_reader: WikipediaReader = WikipediaReader(
        db=db, file_or_url=None, threads=None, categories=settings.CAR_CATEGORIES
    )
    wikipedia_reader_event: Event = asyncio.Event()
    tasks.append(
        asyncio.create_task(
            wikipedia_reader.fetch_process_and_import_data(
                import_data=True, event_to_set=wikipedia_reader_event
            )
        )
    )

    # Import Fuel Data
    eurostat_reader = EurostatFuelReader(
        settings.EUROSTAT_TEST_FUEL_HISTORY_2005_ONWARDS, db=db
    )
    tasks.append(
        asyncio.create_task(
            eurostat_reader.fetch_process_and_import_data(
                import_data=True, event_to_wait=country_codes_reader_event
            )
        )
    )

    # Import CarFuelData
    cfd_reader_test: CarFuelDataReader = CarFuelDataReader(
        db=db, file_to_read=settings.CARFUELDATA_TEST_PATH_OR_URL
    )
    tasks.append(
        asyncio.create_task(
            cfd_reader_test.fetch_process_and_import_data(
                import_data=True,
            )
        )
    )

    # Import and Match Envirocar Data
    envirocar_reader: EnvirocarReader = EnvirocarReader(db=db)
    tasks.append(
        asyncio.create_task(
            envirocar_reader.fetch_process_and_import_data(
                import_data=True, event_to_wait=wikipedia_reader_event
            )
        )
    )

    await asyncio.gather(*tasks)
