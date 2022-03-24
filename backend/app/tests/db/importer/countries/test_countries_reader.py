import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.importer.countries.countries_reader import CountryCodesReader
from app.models import CountryData


@pytest.mark.asyncio
async def test_country_codes_reader(db: Session) -> None:
    country_codes_reader: CountryCodesReader = CountryCodesReader(
        db=db,
        file_to_read=settings.COUNTRY_CODES_TEST_PATH,
        country_geometry_file=settings.COUNTRY_BOUNDARIES_TEST_PATH,
    )
    await country_codes_reader.fetch_process_and_import_data(import_data=False)
    # Actually 250 but Channel Islands get removed since lacking Alpha 2 and 3.
    assert len(country_codes_reader.objects_list) == 249
    country_object: CountryData

    for country_object in country_codes_reader.objects_list:
        assert issubclass(type(country_object), CountryData)
        if len(country_object.__dict__) < 9:
            # No geometries for Caribbean Netherlands, Curacao, Sint Maarten and South Sudan... Sad.
            assert country_object.country_alpha_2 in ["BQ", "CW", "SX", "SS"]
        else:
            assert len(country_object.__dict__) == 9
            assert country_object.geom
        if country_object.id == "UK":
            assert country_object.country_alpha_2 == "UK"
            assert country_object.country_alpha_3 == "GBR"
