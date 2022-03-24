from typing import List

import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.importer.countries.countries_reader import CountryCodesReader
from app.db.importer.fuelprices.eurostat_reader import EurostatFuelReader
from app.models import CountryData, EurostatCountryPrice, EurostatGeneralPrice


@pytest.mark.asyncio
async def test_eurostat_importer(db: Session) -> None:
    # Clean the database
    db.query(EurostatCountryPrice).delete()
    db.query(EurostatGeneralPrice).delete()
    db.query(CountryData).delete()
    db.commit()

    country_codes_reader: CountryCodesReader = CountryCodesReader(
        db=db,
        file_to_read=settings.COUNTRY_CODES_TEST_PATH,
        country_geometry_file=settings.COUNTRY_BOUNDARIES_TEST_PATH,
    )
    await country_codes_reader.fetch_process_and_import_data(import_data=True)
    eurostat_reader = EurostatFuelReader(
        settings.EUROSTAT_TEST_FUEL_HISTORY_2005_ONWARDS, db=db
    )
    await eurostat_reader.fetch_process_and_import_data(import_data=True)

    db_object: EurostatCountryPrice
    country_price_objects: List = [
        db_object
        for db_object in eurostat_reader.objects_list
        if isinstance(db_object, EurostatCountryPrice)
    ]
    general_price_objects: List = [
        db_object
        for db_object in eurostat_reader.objects_list
        if isinstance(db_object, EurostatGeneralPrice)
    ]

    all_country_prices_in_db: List = db.query(EurostatCountryPrice.id).all()
    all_general_prices_in_db: List = db.query(EurostatGeneralPrice.id).all()
    assert len(all_country_prices_in_db) == len(country_price_objects)
    assert len(all_general_prices_in_db) == len(general_price_objects)

    for db_object in eurostat_reader.objects_list:
        db.delete(db_object)
    db.commit()
    for db_object in country_codes_reader.objects_list:
        db.delete(db_object)
    db.commit()


@pytest.mark.asyncio
async def test_eurostat_importer_must_fail(db: Session) -> None:

    eurostat_reader = EurostatFuelReader(
        file_to_read=settings.EUROSTAT_TEST_FUEL_HISTORY_2005_ONWARDS, db=db
    )
    with pytest.raises(FileNotFoundError):
        await eurostat_reader.fetch_process_and_import_data(import_data=False)
