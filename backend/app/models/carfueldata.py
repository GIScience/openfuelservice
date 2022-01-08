import datetime
import hashlib
from typing import Any, Dict, List, Union

from sqlalchemy import (
    ARRAY,
    CHAR,
    Boolean,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    event,
    orm,
)
from sqlalchemy.engine import base

from app.db.base_class import Base
from app.db.importer.mappings import CarFuelDataHeaderMapping


class CarFuelDataCar(Base):
    # carfueldata_cars
    # CarfuelDataCarModel
    # id = hash_id
    id = Column(CHAR(length=32), primary_key=True)
    manufacturer = Column(String, nullable=False, index=True)
    model = Column(String, nullable=False)
    description = Column(String, nullable=True)
    transmission = Column(String, nullable=True)
    engine_capacity = Column(Integer, nullable=True)
    fuel_type = Column(String, nullable=False)
    electric_energy_consumption_miles_kwh = Column(Float, nullable=True)
    manual_or_automatic = Column(String, nullable=True)
    powertrain = Column(String, nullable=True)
    engine_power_ps = Column(Float, nullable=True)
    engine_power_kw = Column(Float, nullable=True)
    wh_km = Column(Float, nullable=True)
    maximum_range_km = Column(Float, nullable=True)
    maximum_range_miles = Column(Float, nullable=True)
    euro_standard = Column(String, nullable=True)
    diesel_ved_supplement = Column(Boolean, nullable=True)
    testing_scheme = Column(String, nullable=True)
    wltp_imperial_low = Column(Float, nullable=True)
    wltp_imperial_medium = Column(Float, nullable=True)
    wltp_imperial_high = Column(Float, nullable=True)
    wltp_imperial_extra_high = Column(Float, nullable=True)
    wltp_imperial_combined = Column(Float, nullable=True)
    wltp_imperial_combined_weighted = Column(Float, nullable=True)
    wltp_metric_low = Column(Float, nullable=True)
    wltp_metric_medium = Column(Float, nullable=True)
    wltp_metric_high = Column(Float, nullable=True)
    wltp_metric_extra_high = Column(Float, nullable=True)
    wltp_metric_combined = Column(Float, nullable=True)
    wltp_metric_combined_weighted = Column(Float, nullable=True)
    wltp_co2 = Column(Integer, nullable=True)
    wltp_co2_weighted = Column(Integer, nullable=True)
    equivalent_all_electric_range_miles = Column(Integer, nullable=True)
    equivalent_all_electric_range_km = Column(Integer, nullable=True)
    electric_range_city_miles = Column(Integer, nullable=True)
    electric_range_city_km = Column(Integer, nullable=True)
    emissions_co_mg_km = Column(Float, nullable=True)
    thc_emissions_mg_km = Column(Float, nullable=True)
    emissions_nox_mg_km = Column(Float, nullable=True)
    thc_nox_emissions_mg_km = Column(Float, nullable=True)
    particulates_no_mg_km = Column(Float, nullable=True)
    rde_nox_urban = Column(Integer, nullable=True)
    rde_nox_combined = Column(Integer, nullable=True)
    noise_level_dba = Column(Float, nullable=True)
    wiki_hashes = Column(ARRAY(CHAR(length=32)), nullable=True)
    date_of_change = Column(Date, nullable=False)
    year = Column(Integer, nullable=True)

    @staticmethod
    def _check_name_for_year(car_name: str) -> Union[int, None]:
        now = datetime.datetime.now()
        max_year = int(now.year)
        min_year = 1980
        while True:
            if max_year < min_year:
                return None
            elif str(max_year) in car_name:
                return max_year
            else:
                max_year -= 1

    def set_data(self, data: List, headers: Dict) -> None:
        value: Any
        key: CarFuelDataHeaderMapping
        for key, header_index in headers.items():
            value = data[header_index]
            if value is None or str(value).lower().strip() == "n/a" or key is None:
                value = None
            elif key == CarFuelDataHeaderMapping.DATE_OF_CHANGE:
                value: datetime = (datetime.datetime.strptime(value, "%d %B %Y"))  # type: ignore
                if "year" not in self.__dict__.keys() or (
                    "year" in self.__dict__.keys() and self.__dict__.get("year") is None
                ):
                    self.__setattr__("year", value.year)
            elif key == CarFuelDataHeaderMapping.MODEL and type(value) == str:
                if value == "Model X":
                    print()
                year: int = self._check_name_for_year(car_name=value)  # type: ignore
                if year:
                    self.__setattr__("year", year)
            elif type(value) == str and not len(value):
                value = None
            elif type(value) == str and value.isdigit():
                value = float(value)
            elif type(value) == str and value.lower() in ["true", "yes", "no", "false"]:
                value = bool(value)
            self.__setattr__(key.name.lower(), value)

    def hash_object(self) -> str:
        hash_string: str = ""
        key: str
        value: Any
        for key, value in self.__dict__.items():
            if key.startswith("_") or (key == "id"):
                continue
            elif isinstance(value, datetime.datetime) or isinstance(
                value, datetime.date
            ):
                value = value.strftime("%Y%m%d")
            hash_string = f"{hash_string}{str(key.lower())}={str(value).strip()}"
        return hashlib.md5(hash_string.strip(" ").encode("utf-8")).hexdigest()


@event.listens_for(CarFuelDataCar, "before_insert")
def generate_carfueldatacar_id(
    _: orm.Mapper, __: base.Connection, target: CarFuelDataCar
) -> None:
    key: str
    value: Any
    target.id = target.hash_object()


class CarFuelDataAverageCategoryStatistics(Base):
    # cfd_average_category_statistics
    # CarFuelDataAverageCategoryStatisticsModel
    id = Column(CHAR(length=32), primary_key=True, index=True)
    vehicle_type = Column(String, nullable=False, index=True)
    fuel_type = Column(String, nullable=False, index=True)
    phenomenon_name = Column(String, nullable=False, index=True)
    value = Column(Float, nullable=False)
    numb_cars = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False, index=True)
    category_short_eu = Column(
        String, ForeignKey("{}.category_short_eu".format("wikicarcategory"))
    )
