from typing import Dict, List

import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.importer.countries.countries_reader import CountryCodesReader
from app.models import CountryData


@pytest.mark.asyncio
async def test_countries_importer(db: Session) -> None:
    # Clean the database

    country_codes_reader: CountryCodesReader = CountryCodesReader(
        db=db,
        file_to_read=settings.COUNTRY_CODES_TEST_PATH,
        country_geometry_file=settings.COUNTRY_BOUNDARIES_TEST_PATH,
    )
    await country_codes_reader.fetch_process_and_import_data(import_data=True)
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

    for db_object in country_codes_reader.objects_list:
        db.delete(db_object)
    db.commit()
