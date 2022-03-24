import datetime
from typing import Union

import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.importer.countries.countries_reader import CountryCodesReader
from app.db.importer.fuelprices.eurostat_reader import EurostatFuelReader
from app.models import EurostatCountryPrice, EurostatGeneralPrice


@pytest.mark.asyncio
async def test_eurostat_reader(db: Session) -> None:
    # Clean the database
    country_codes_reader: CountryCodesReader = CountryCodesReader(
        db=db,
        file_to_read=settings.COUNTRY_CODES_TEST_PATH,
        country_geometry_file=settings.COUNTRY_BOUNDARIES_TEST_PATH,
    )
    await country_codes_reader.fetch_process_and_import_data(import_data=True)
    eurostat_reader = EurostatFuelReader(
        settings.EUROSTAT_TEST_FUEL_HISTORY_2005_ONWARDS, db=db
    )
    await eurostat_reader.fetch_process_and_import_data(import_data=False)
    db_object: Union[EurostatCountryPrice, EurostatGeneralPrice]
    for db_object in eurostat_reader.objects_list:
        if isinstance(db_object, EurostatCountryPrice):
            assert db_object.country_alpha_2
            assert db_object.taux
        assert db_object.id is not None
        assert isinstance(db_object.id, datetime.datetime)
        assert isinstance(db_object.date, datetime.datetime)
        assert db_object.date == db_object.id
        assert db_object.euro_ttc
        assert db_object.euro_ht
        assert db_object.euro_quantity
        assert db_object.euro_unit
        assert db_object.diesel_ttc
        assert db_object.diesel_ht
        assert db_object.diesel_quantity
        assert db_object.diesel_unit
        assert db_object.price_in_euro
        assert db_object.is_valid

    for db_object in country_codes_reader.objects_list:
        db.delete(db_object)
    db.commit()
