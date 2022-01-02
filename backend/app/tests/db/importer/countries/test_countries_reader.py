from app.core.config import settings
from app.db.importer.countries.countries_reader import CountryCodesReader
from app.models import CountryData


def test_country_codes_reader() -> None:
    country_codes_reader: CountryCodesReader = CountryCodesReader(
        settings.COUNTRY_CODES_PATH
    )
    country_codes_reader.fetch_and_process_data()
    # Actually 250 but Channel Islands get removed since lacking Alpha 2 and 3.
    assert len(country_codes_reader.objects_list) == 249
    country_object: CountryData
    for country_object in country_codes_reader.objects_list:
        assert issubclass(type(country_object), CountryData)
        assert len(country_object.__dict__) == 8
        assert not country_object.geom
        assert country_object.id == country_object.country_alpha_2

    country_codes_reader.enrich_with_geometries(settings.COUNTRY_BOUNDARIES_PATH)
    for country_object in country_codes_reader.objects_list:
        assert issubclass(type(country_object), CountryData)
        if len(country_object.__dict__) < 9:
            # No geometries for Caribbean Netherlands, Curacao, Sint Maarten and South Sudan... Sad.
            assert country_object.country_alpha_2 in ["BQ", "CW", "SX", "SS"]
        else:
            assert len(country_object.__dict__) == 9
            assert country_object.geom
