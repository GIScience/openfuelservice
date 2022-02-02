import datetime
from typing import Union

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.importer.base_importer import BaseImporter
from app.db.importer.countries.countries_reader import CountryCodesReader
from app.db.importer.fuelprices.eurostat_reader import EurostatFuelReader
from app.models import EurostatCountryPrice, EurostatGeneralPrice


def test_eurostat_reader(db: Session) -> None:
    # Clean the database
    db.query(EurostatCountryPrice).delete()
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
