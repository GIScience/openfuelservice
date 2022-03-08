import logging
from enum import Enum
from typing import Union

logger = logging.getLogger(__name__)


class BaseMapping(Enum):
    @classmethod
    def from_value(cls, type_to_check: str) -> Union[Enum, None]:
        check_to_lower = type_to_check.casefold().strip()
        for fuel_type in cls:
            value: Union[str, tuple] = fuel_type.value
            if type(value) == str and check_to_lower == value.casefold().strip():
                return fuel_type
            elif type(value) == tuple:
                for sub_mapping in value:
                    if check_to_lower == sub_mapping.casefold().strip():
                        return fuel_type
        return None


class EurostatSheetMapping(BaseMapping):
    PRICES_WITH_TAXES_PER_CTR = "Prices with taxes, per CTR"
    PRICES_WO_TAXES_PER_CTR = "Prices wo taxes, per CTR"
    PRICES_WITH_TAXES_EU = "Prices with taxes, EU"
    PRICES_WO_TAXES_EU = "Prices wo taxes, EU"
    PRICES_WITH_TAXES_UK = "Prices with taxes, UK"
    PRICES_WO_TAXES_UK = "Prices wo taxes, UK"


class CountriesMapping(BaseMapping):
    COUNTRY_NAME = "CLDR display name"
    COUNTRY_ALPHA_2 = "ISO3166-1-Alpha-2", "ISO2"
    COUNTRY_ALPHA_3 = "ISO3166-1-Alpha-3", "ISO3"
    COUNTRY_NUMERIC = "ISO3166-1-numeric"
    COUNTRY_CURRENCY_CODE = "ISO4217-currency_alphabetic_code"
    COUNTRY_CURRENCY_NAME = "ISO4217-currency_name"


class CarFuelDataHeaderMapping(BaseMapping):
    MANUFACTURER = "Manufacturer"
    MODEL = "Model"
    DESCRIPTION = "Description"
    TRANSMISSION = "Transmission"
    MANUAL_OR_AUTOMATIC = "Manual or Automatic"
    ENGINE_CAPACITY = "Engine Capacity"
    FUEL_TYPE = "Fuel Type"
    POWERTRAIN = "Powertrain"
    ENGINE_POWER_PS = "Engine Power (PS)"
    ENGINE_POWER_KW = "Engine Power (Kw)"
    ELECTRIC_ENERGY_CONSUMPTION_MILES_KWH = "Electric energy consumption Miles/kWh"
    WH_KM = "wh/km"
    MAXIMUM_RANGE_KM = "Maximum range (Km)"
    MAXIMUM_RANGE_MILES = "Maximum range (Miles)"
    EURO_STANDARD = "Euro Standard"
    DIESEL_VED_SUPPLEMENT = "Diesel VED Supplement"
    TESTING_SCHEME = "Testing Scheme"
    WLTP_IMPERIAL_LOW = "WLTP Imperial Low"
    WLTP_IMPERIAL_MEDIUM = "WLTP Imperial Medium"
    WLTP_IMPERIAL_HIGH = "WLTP Imperial High"
    WLTP_IMPERIAL_EXTRA_HIGH = "WLTP Imperial Extra High"
    WLTP_IMPERIAL_COMBINED = "WLTP Imperial Combined"
    WLTP_IMPERIAL_COMBINED_WEIGHTED = "WLTP Imperial Combined (Weighted)"
    WLTP_METRIC_LOW = "WLTP Metric Low"
    WLTP_METRIC_MEDIUM = "WLTP Metric Medium"
    WLTP_METRIC_HIGH = "WLTP Metric High"
    WLTP_METRIC_EXTRA_HIGH = "WLTP Metric Extra High"
    WLTP_METRIC_COMBINED = "WLTP Metric Combined"
    WLTP_METRIC_COMBINED_WEIGHTED = "WLTP Metric Combined (Weighted)"
    WLTP_CO2 = "WLTP CO2"
    WLTP_CO2_WEIGHTED = "WLTP CO2 Weighted"
    EQUIVALENT_ALL_ELECTRIC_RANGE_MILES = "Equivalent All Electric Range Miles"
    EQUIVALENT_ALL_ELECTRIC_RANGE_KM = "Equivalent All Electric Range KM"
    ELECTRIC_RANGE_CITY_MILES = "Electric Range City Miles"
    ELECTRIC_RANGE_CITY_KM = "Electric Range City Km"
    EMISSIONS_CO_MG_KM = "Emissions CO [mg/km]"
    THC_EMISSIONS_MG_KM = "THC Emissions [mg/km]"
    EMISSIONS_NOX_MG_KM = "Emissions NOx [mg/km]"
    THC_NOX_EMISSIONS_MG_KM = "THC + NOx Emissions [mg/km]"
    PARTICULATES_NO_MG_KM = "Particulates [No.] [mg/km]"
    RDE_NOX_URBAN = "RDE NOx Urban"
    RDE_NOX_COMBINED = "RDE NOx Combined"
    NOISE_LEVEL_DBA = "Noise Level dB(A)"
    DATE_OF_CHANGE = "Date of change"


class FuelMappings(BaseMapping):
    DIESEL: str = "diesel"
    DIESEL_ELECTRIC: tuple = ("diesel electric", "electricity / diesel")
    GASOLINE: tuple = ("gasoline", "Petrol", "gas", "petrol / lpg")
    GASOLINE_ELECTRIC: tuple = (
        "gasoline_electric",
        "electricity / petrol",
        "petrol electric",
        "petrol hybrid",
    )
    ELECTRIC: str = "Electricity"
