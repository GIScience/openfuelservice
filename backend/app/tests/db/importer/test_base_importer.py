from typing import List

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.importer.base_importer import BaseImporter
from app.db.importer.carfueldata.cfd_reader import CarFuelDataReader
from app.db.importer.countries.countries_reader import CountryCodesReader
from app.models import CarFuelDataCar, CountryData


def test_base_cfd_importer(db: Session) -> None:
    cfd_reader_test: CarFuelDataReader = CarFuelDataReader(
        settings.CARFUELDATA_TEST_PATH_OR_URL
    )
    cfd_reader_test.fetch_and_process_data()
    BaseImporter(db=db).import_data(reader_object=cfd_reader_test)
    car: CarFuelDataCar
    unique_ids: List = list(set([car.id for car in cfd_reader_test.objects_list]))
    assert len(
        CarFuelDataCar.get_all_by_filter(db=db, filter_ids=unique_ids, id_only=True)
    ) == len(unique_ids)


def test_base_countries_importer(db: Session) -> None:
    country_codes_reader: CountryCodesReader = CountryCodesReader(
        settings.COUNTRY_CODES_PATH
    )
    country_codes_reader.fetch_and_process_data()
    country_codes_reader.enrich_with_geometries(settings.COUNTRY_BOUNDARIES_PATH)
    BaseImporter(db=db).import_data(reader_object=country_codes_reader)
    country: CountryData
    unique_ids: List = list(
        set([country.country_alpha_2 for country in country_codes_reader.objects_list])
    )
    assert len(
        CountryData.get_all_by_filter(db=db, filter_ids=unique_ids, id_only=True)
    ) == len(unique_ids)
    source_country: CountryData
    for source_country in country_codes_reader.objects_list:
        assert source_country.id in unique_ids
        assert source_country.country_alpha_2 in unique_ids
