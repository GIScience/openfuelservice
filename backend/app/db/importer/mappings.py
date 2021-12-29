import logging
from enum import Enum

logger = logging.getLogger(__name__)


class CFDHeaderMapping(Enum):
    MANUFACTURER = 'Manufacturer'
    MODEL = 'Model'
    DESCRIPTION = 'Description'
    TRANSMISSION = 'Transmission'
    MANUAL_OR_AUTOMATIC = 'Manual or Automatic'
    ENGINE_CAPACITY = 'Engine Capacity'
    FUEL_TYPE = 'Fuel Type'
    POWERTRAIN = 'Powertrain'
    ENGINE_POWER_PS = 'Engine Power (PS)'
    ENGINE_POWER_KW = 'Engine Power (Kw)'
    ELECTRIC_ENERGY_CONSUMPTION_MILES_KWH = 'Electric energy consumption Miles/kWh'
    WH_KM = 'wh/km'
    MAXIMUM_RANGE_KM = 'Maximum range (Km)'
    MAXIMUM_RANGE_MILES = 'Maximum range (Miles)'
    EURO_STANDARD = 'Euro Standard'
    DIESEL_VED_SUPPLEMENT = 'Diesel VED Supplement'
    TESTING_SCHEME = 'Testing Scheme'
    WLTP_IMPERIAL_LOW = 'WLTP Imperial Low'
    WLTP_IMPERIAL_MEDIUM = 'WLTP Imperial Medium'
    WLTP_IMPERIAL_HIGH = 'WLTP Imperial High'
    WLTP_IMPERIAL_EXTRA_HIGH = 'WLTP Imperial Extra High'
    WLTP_IMPERIAL_COMBINED = 'WLTP Imperial Combined'
    WLTP_IMPERIAL_COMBINED_WEIGHTED = 'WLTP Imperial Combined (Weighted)'
    WLTP_METRIC_LOW = 'WLTP Metric Low'
    WLTP_METRIC_MEDIUM = 'WLTP Metric Medium'
    WLTP_METRIC_HIGH = 'WLTP Metric High'
    WLTP_METRIC_EXTRA_HIGH = 'WLTP Metric Extra High'
    WLTP_METRIC_COMBINED = 'WLTP Metric Combined'
    WLTP_METRIC_COMBINED_WEIGHTED = 'WLTP Metric Combined (Weighted)'
    WLTP_CO2 = 'WLTP CO2'
    WLTP_CO2_WEIGHTED = 'WLTP CO2 Weighted'
    EQUIVALENT_ALL_ELECTRIC_RANGE_MILES = 'Equivalent All Electric Range Miles'
    EQUIVALENT_ALL_ELECTRIC_RANGE_KM = 'Equivalent All Electric Range KM'
    ELECTRIC_RANGE_CITY_MILES = 'Electric Range City Miles'
    ELECTRIC_RANGE_CITY_KM = 'Electric Range City Km'
    EMISSIONS_CO_MG_KM = 'Emissions CO [mg/km]'
    THC_EMISSIONS_MG_KM = 'THC Emissions [mg/km]'
    EMISSIONS_NOX_MG_KM = 'Emissions NOx [mg/km]'
    THC_NOX_EMISSIONS_MG_KM = 'THC + NOx Emissions [mg/km]'
    PARTICULATES_NO_MG_KM = 'Particulates [No.] [mg/km]'
    RDE_NOX_URBAN = 'RDE NOx Urban'
    RDE_NOX_COMBINED = 'RDE NOx Combined'
    NOISE_LEVEL_DBA = 'Noise Level dB(A)'
    DATE_OF_CHANGE = 'Date of change'

    @classmethod
    def from_value(cls, value: str) -> Enum | None:
        check_to_lower = value.casefold().strip()
        for header_value in CFDHeaderMapping:
            value: str = header_value.value
            if check_to_lower == value.casefold().strip():
                return header_value
        return None


class FuelMappings(Enum):
    DIESEL: str = "diesel"
    DIESEL_ELECTRIC: tuple = ("diesel electric", "electricity / diesel")
    GASOLINE: tuple = ("gasoline", "Petrol", "gas")
    GASOLINE_ELECTRIC: tuple = (
        "gasoline_electric",
        "electricity / petrol",
        "petrol electric",
        "petrol hybrid",
    )
    ELECTRIC: str = "Electricity"

    @classmethod
    def from_fuel_type(cls, type_to_check: str) -> Enum | None:
        check_to_lower = type_to_check.casefold().strip()
        for fuel_type in FuelMappings:
            value: str | tuple = fuel_type.value
            if type(value) == str and check_to_lower == value.casefold().strip():
                return fuel_type
            elif type(value) == tuple:
                for sub_mapping in value:
                    if check_to_lower == sub_mapping.casefold().strip():
                        return fuel_type
        return None
