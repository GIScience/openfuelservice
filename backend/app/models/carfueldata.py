import datetime
import hashlib

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
)
from sqlalchemy.orm import Session

from app.db.base_class import Base
from app.db.importer.carfueldata.cfd_objects import CFDImportCar


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

    @classmethod
    def get_all_by_filter(cls, db: Session, filter_ids: list) -> list:
        return db.query(cls.id).filter(cls.id.in_(filter_ids)).all()

    def translate_import(self, cfd_import_car: CFDImportCar) -> None:
        value: float | bool | str | None
        key: str
        unwanted_chars = "!#$%^&*()"
        hash_string: str = ""
        for key, value in cfd_import_car.__dict__.items():
            for unwantedChar in unwanted_chars:
                key = key.strip().replace(unwantedChar, "_").replace(" ", "_")
            if type(value) == str and value.isdigit():
                value = float(value)
            elif type(value) == str and value.lower() in ["true", "yes", "no", "false"]:
                value = bool(value)
            elif type(value) == str and not len(value):
                value = None
            self.__dict__[key] = value
            if isinstance(value, datetime.date):
                hash_string = f"{hash_string}{str(key)}={value.strftime('%Y%m%d')}"
            else:
                hash_string = f"{hash_string}{str(key)}={str(value).strip()}"

        self.id = hashlib.md5(
            hash_string.casefold().strip(" ").encode("utf-8")
        ).hexdigest()


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
