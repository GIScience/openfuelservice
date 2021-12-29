import pytest

from app.db.importer.mappings import FuelMappings


@pytest.mark.parametrize(
    "fuel_type_to_check,fuel_type_to_get",
    (
        ("diesel", FuelMappings.DIESEL),
        ("diesel electric", FuelMappings.DIESEL_ELECTRIC),
        ("electricity / diesel", FuelMappings.DIESEL_ELECTRIC),
        ("gasoline", FuelMappings.GASOLINE),
        ("Petrol", FuelMappings.GASOLINE),
        ("gas", FuelMappings.GASOLINE),
        ("gasoline_electric", FuelMappings.GASOLINE_ELECTRIC),
        ("electricity / petrol", FuelMappings.GASOLINE_ELECTRIC),
        ("petrol electric", FuelMappings.GASOLINE_ELECTRIC),
        ("petrol hybrid", FuelMappings.GASOLINE_ELECTRIC),
        ("Electricity", FuelMappings.ELECTRIC),
        ("Foobar", None),
    ),
)
def test_from_fuel_type(
    fuel_type_to_check: str, fuel_type_to_get: FuelMappings
) -> None:
    assert FuelMappings.from_fuel_type(fuel_type_to_check) == fuel_type_to_get
