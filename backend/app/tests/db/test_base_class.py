from app.db.base_class import Base
from app.db.importer.mappings import CountriesMapping


def test_base_class() -> None:
    test_base = Base()
    test_base.set_data([22], {CountriesMapping.COUNTRY_NUMERIC: 0})
    assert test_base.__dict__["country_numeric"] == 22
    assert len(test_base.__dict__) == 1
