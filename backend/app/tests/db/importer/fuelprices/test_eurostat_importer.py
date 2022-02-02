from typing import List

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.importer.base_importer import BaseImporter
from app.db.importer.countries.countries_reader import CountryCodesReader
from app.db.importer.fuelprices.eurostat_reader import EurostatFuelReader
from app.models import EurostatCountryPrice, EurostatGeneralPrice


def test_eurostat_importer(db: Session) -> None:
    # Clean the database
    db.query(EurostatCountryPrice).delete()
    db.query(EurostatGeneralPrice).delete()
    db.commit()

    country_codes_reader: CountryCodesReader = CountryCodesReader(
        settings.COUNTRY_CODES_TEST_PATH
    )
    country_codes_reader.fetch_and_process_data()
    BaseImporter(db=db).import_data(db_objects=country_codes_reader.objects_list)
    eurostat_reader = EurostatFuelReader(
        settings.EUROSTAT_TEST_FUEL_HISTORY_2005_ONWARDS, db=db
    )
    eurostat_reader.fetch_and_process_data()

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

    BaseImporter(db=db).import_data(db_objects=eurostat_reader.objects_list)

    all_country_prices_in_db: List = db.query(EurostatCountryPrice.id).all()
    all_general_prices_in_db: List = db.query(EurostatGeneralPrice.id).all()
    assert len(all_country_prices_in_db) == len(country_price_objects)
    assert len(all_general_prices_in_db) == len(general_price_objects)
