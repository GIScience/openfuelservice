from datetime import datetime
from typing import Any, Union

from app.db.importer.mappings import CFDHeaderMapping


class CFDImportCar:
    def __init__(self) -> None:
        self.manufacturer = None
        self.model = None
        self.description = None
        self.transmission = None
        self.manual_or_automatic = None
        self.engine_capacity = None
        self.fuel_type = None
        self.powertrain = None
        self.engine_power_ps = None
        self.engine_power_kw = None
        self.electric_energy_consumption_miles_kwh = None
        self.wh_km = None
        self.maximum_range_km = None
        self.maximum_range_miles = None
        self.euro_standard = None
        self.diesel_ved_supplement = None
        self.testing_scheme = None
        self.wltp_imperial_low = None
        self.wltp_imperial_medium = None
        self.wltp_imperial_high = None
        self.wltp_imperial_extra_high = None
        self.wltp_imperial_combined = None
        self.wltp_imperial_combined_weighted = None
        self.wltp_metric_low = None
        self.wltp_metric_medium = None
        self.wltp_metric_high = None
        self.wltp_metric_extra_high = None
        self.wltp_metric_combined = None
        self.wltp_metric_combined_weighted = None
        self.wltp_co2 = None
        self.wltp_co2_weighted = None
        self.equivalent_all_electric_range_miles = None
        self.equivalent_all_electric_range_km = None
        self.electric_range_city_miles = None
        self.electric_range_city_km = None
        self.emissions_co_mg_km = None
        self.thc_emissions_mg_km = None
        self.emissions_nox_mg_km = None
        self.thc_nox_emissions_mg_km = None
        self.particulates_no_mg_km = None
        self.rde_nox_urban = None
        self.rde_nox_combined = None
        self.noise_level_dba = None
        self.date_of_change = None
        self._year: int = 0
        self.wiki_hashes = None

    @property
    def year(self) -> int:
        return self._year

    @year.setter
    def year(self, value: int) -> None:
        self._year = value

    @staticmethod
    def _check_name_for_year(car_name: str) -> Union[int, None]:
        import datetime

        now = datetime.datetime.now()
        max_year = int(now.year)
        min_year = 1980
        search_year = max_year
        while True:
            if search_year < min_year:
                return None
            elif str(search_year) in car_name:
                return search_year
            else:
                search_year -= 1

    def __setattr__(self, key: str, value: Any) -> None:
        if value is None or str(value).lower().strip() == "n/a":
            return
        elif key.lower().strip() == CFDHeaderMapping.DATE_OF_CHANGE.value.lower():
            value: datetime = (datetime.strptime(value, "%d %B %Y"))  # type: ignore
            if "year" not in self.__dict__ or (
                "year" in self.__dict__ and self.year is None
            ):
                self.year = value.year
        elif key.lower().strip() == "year" and type(value) == str:
            value: int = self._check_name_for_year(car_name=value)  # type: ignore
        elif key in self.__dict__ and self.__dict__[key] is not None:
            return
        self.__dict__[key] = value
