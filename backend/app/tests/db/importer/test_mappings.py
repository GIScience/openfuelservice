import pytest

from app.db.importer.mappings import (
    CarFuelDataHeaderMapping,
    CountriesMapping,
    EurostatSheetMapping,
    FuelMappings,
)


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
    assert FuelMappings.from_value(fuel_type_to_check) == fuel_type_to_get


@pytest.mark.parametrize(
    "fuel_type_to_check,fuel_type_to_get",
    (
        ("Prices with taxes, per CTR", EurostatSheetMapping.PRICES_WITH_TAXES_PER_CTR),
        ("Prices wo taxes, per CTR", EurostatSheetMapping.PRICES_WO_TAXES_PER_CTR),
        ("Prices with taxes, EU", EurostatSheetMapping.PRICES_WITH_TAXES_EU),
        ("Prices wo taxes, EU", EurostatSheetMapping.PRICES_WO_TAXES_EU),
        ("Prices with taxes, UK", EurostatSheetMapping.PRICES_WITH_TAXES_UK),
        ("Prices wo taxes, UK", EurostatSheetMapping.PRICES_WO_TAXES_UK),
        ("Foobar", None),
    ),
)
def test_eurostat_sheet_mapping(
    fuel_type_to_check: str, fuel_type_to_get: EurostatSheetMapping
) -> None:
    assert EurostatSheetMapping.from_value(fuel_type_to_check) == fuel_type_to_get


@pytest.mark.parametrize(
    "fuel_type_to_check,fuel_type_to_get",
    (
        ("CLDR display name", CountriesMapping.COUNTRY_NAME),
        ("ISO3166-1-Alpha-2", CountriesMapping.COUNTRY_ALPHA_2),
        ("ISO2", CountriesMapping.COUNTRY_ALPHA_2),
        ("ISO3166-1-Alpha-3", CountriesMapping.COUNTRY_ALPHA_3),
        ("ISO3", CountriesMapping.COUNTRY_ALPHA_3),
        ("ISO3166-1-numeric", CountriesMapping.COUNTRY_NUMERIC),
        ("ISO4217-currency_alphabetic_code", CountriesMapping.COUNTRY_CURRENCY_CODE),
        ("ISO4217-currency_name", CountriesMapping.COUNTRY_CURRENCY_NAME),
        ("Foobar", None),
    ),
)
def test_countries_mapping(
    fuel_type_to_check: str, fuel_type_to_get: CountriesMapping
) -> None:
    assert CountriesMapping.from_value(fuel_type_to_check) == fuel_type_to_get


@pytest.mark.parametrize(
    "fuel_type_to_check,fuel_type_to_get",
    (
        ("Manufacturer", CarFuelDataHeaderMapping.MANUFACTURER),
        ("Model", CarFuelDataHeaderMapping.MODEL),
        ("Description", CarFuelDataHeaderMapping.DESCRIPTION),
        ("Transmission", CarFuelDataHeaderMapping.TRANSMISSION),
        ("Manual or Automatic", CarFuelDataHeaderMapping.MANUAL_OR_AUTOMATIC),
        ("Engine Capacity", CarFuelDataHeaderMapping.ENGINE_CAPACITY),
        ("Fuel Type", CarFuelDataHeaderMapping.FUEL_TYPE),
        ("Powertrain", CarFuelDataHeaderMapping.POWERTRAIN),
        ("Engine Power (PS)", CarFuelDataHeaderMapping.ENGINE_POWER_PS),
        ("Engine Power (Kw)", CarFuelDataHeaderMapping.ENGINE_POWER_KW),
        (
            "Electric energy consumption Miles/kWh",
            CarFuelDataHeaderMapping.ELECTRIC_ENERGY_CONSUMPTION_MILES_KWH,
        ),
        ("wh/km", CarFuelDataHeaderMapping.WH_KM),
        ("Maximum range (Km)", CarFuelDataHeaderMapping.MAXIMUM_RANGE_KM),
        ("Maximum range (Miles)", CarFuelDataHeaderMapping.MAXIMUM_RANGE_MILES),
        ("Euro Standard", CarFuelDataHeaderMapping.EURO_STANDARD),
        ("Diesel VED Supplement", CarFuelDataHeaderMapping.DIESEL_VED_SUPPLEMENT),
        ("Testing Scheme", CarFuelDataHeaderMapping.TESTING_SCHEME),
        ("WLTP Imperial Low", CarFuelDataHeaderMapping.WLTP_IMPERIAL_LOW),
        ("WLTP Imperial Medium", CarFuelDataHeaderMapping.WLTP_IMPERIAL_MEDIUM),
        ("WLTP Imperial High", CarFuelDataHeaderMapping.WLTP_IMPERIAL_HIGH),
        ("WLTP Imperial Extra High", CarFuelDataHeaderMapping.WLTP_IMPERIAL_EXTRA_HIGH),
        ("WLTP Imperial Combined", CarFuelDataHeaderMapping.WLTP_IMPERIAL_COMBINED),
        (
            "WLTP Imperial Combined (Weighted)",
            CarFuelDataHeaderMapping.WLTP_IMPERIAL_COMBINED_WEIGHTED,
        ),
        ("WLTP Metric Low", CarFuelDataHeaderMapping.WLTP_METRIC_LOW),
        ("WLTP Metric Medium", CarFuelDataHeaderMapping.WLTP_METRIC_MEDIUM),
        ("WLTP Metric High", CarFuelDataHeaderMapping.WLTP_METRIC_HIGH),
        ("WLTP Metric Extra High", CarFuelDataHeaderMapping.WLTP_METRIC_EXTRA_HIGH),
        ("WLTP Metric Combined", CarFuelDataHeaderMapping.WLTP_METRIC_COMBINED),
        (
            "WLTP Metric Combined (Weighted)",
            CarFuelDataHeaderMapping.WLTP_METRIC_COMBINED_WEIGHTED,
        ),
        ("WLTP CO2", CarFuelDataHeaderMapping.WLTP_CO2),
        ("WLTP CO2 Weighted", CarFuelDataHeaderMapping.WLTP_CO2_WEIGHTED),
        (
            "Equivalent All Electric Range Miles",
            CarFuelDataHeaderMapping.EQUIVALENT_ALL_ELECTRIC_RANGE_MILES,
        ),
        (
            "Equivalent All Electric Range KM",
            CarFuelDataHeaderMapping.EQUIVALENT_ALL_ELECTRIC_RANGE_KM,
        ),
        (
            "Electric Range City Miles",
            CarFuelDataHeaderMapping.ELECTRIC_RANGE_CITY_MILES,
        ),
        ("Electric Range City Km", CarFuelDataHeaderMapping.ELECTRIC_RANGE_CITY_KM),
        ("Emissions CO [mg/km]", CarFuelDataHeaderMapping.EMISSIONS_CO_MG_KM),
        ("THC Emissions [mg/km]", CarFuelDataHeaderMapping.THC_EMISSIONS_MG_KM),
        ("Emissions NOx [mg/km]", CarFuelDataHeaderMapping.EMISSIONS_NOX_MG_KM),
        (
            "THC + NOx Emissions [mg/km]",
            CarFuelDataHeaderMapping.THC_NOX_EMISSIONS_MG_KM,
        ),
        ("Particulates [No.] [mg/km]", CarFuelDataHeaderMapping.PARTICULATES_NO_MG_KM),
        ("RDE NOx Urban", CarFuelDataHeaderMapping.RDE_NOX_URBAN),
        ("RDE NOx Combined", CarFuelDataHeaderMapping.RDE_NOX_COMBINED),
        ("Noise Level dB(A)", CarFuelDataHeaderMapping.NOISE_LEVEL_DBA),
        ("Date of change", CarFuelDataHeaderMapping.DATE_OF_CHANGE),
        ("Foobar", None),
    ),
)
def test_carfueldata_header_mapping(
    fuel_type_to_check: str, fuel_type_to_get: CarFuelDataHeaderMapping
) -> None:
    assert CarFuelDataHeaderMapping.from_value(fuel_type_to_check) == fuel_type_to_get
