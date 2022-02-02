from typing import Dict, List

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.importer.base_importer import BaseImporter
from app.db.importer.countries.countries_reader import CountryCodesReader
from app.models import CountryData


def test_countries_importer(db: Session) -> None:
    # Clean the database
    db.query(CountryData).delete()
    db.commit()

    country_codes_reader: CountryCodesReader = CountryCodesReader(
        settings.COUNTRY_CODES_TEST_PATH
    )
    country_codes_reader.fetch_and_process_data()
    country_codes_reader.enrich_with_geometries(settings.COUNTRY_BOUNDARIES_TEST_PATH)
    BaseImporter(db=db).import_data(db_objects=country_codes_reader.objects_list)
    country: CountryData
    unique_ids: List = list(
        set([country.country_alpha_2 for country in country_codes_reader.objects_list])
    )
    unique_ids_db = CountryData.get_all_by_filter(
        db=db, filter_ids=unique_ids, id_only=True
    )
    assert len(unique_ids_db) == len(unique_ids)
    source_country: Dict
    for source_country in unique_ids_db:
        assert source_country[0] in unique_ids

    CountryData.__table__.delete().where(CountryData.id.in_([unique_ids]))
