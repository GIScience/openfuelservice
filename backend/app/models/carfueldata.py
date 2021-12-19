from sqlalchemy import ARRAY, CHAR, Column, Date, Float, ForeignKey, Integer, String

from app.db.base_class import Base


class CarfuelDataCar(Base):
    # carfueldata_cars
    # CarfuelDataCarModel
    # id = hash_id
    id = Column(CHAR(length=32), primary_key=True)
    manufacturer = Column(String, nullable=False, index=True)
    model = Column(String, nullable=False)
    description = Column(String, nullable=False)
    transmission = Column(String, nullable=False)
    engine_capacity = Column(String, nullable=False)
    fuel_type = Column(String, nullable=False)
    e_consumption_miles_per_kWh = Column(Float, nullable=True)
    e_consumption_wh_per_km = Column(Float, nullable=True)
    maximum_range_km = Column(Float, nullable=True)
    maximum_range_miles = Column(Float, nullable=True)
    metric_urban_cold = Column(Float, nullable=True)
    metric_extra_urban = Column(Float, nullable=True)
    metric_combined = Column(Float, nullable=True)
    imperial_urban_cold = Column(Float, nullable=True)
    imperial_extra_urban = Column(Float, nullable=True)
    imperial_combined = Column(Float, nullable=True)
    co2_g_per_km = Column(Float, nullable=True)
    fuel_cost_6000_miles = Column(Float, nullable=True)
    fuel_cost_12000_miles = Column(Float, nullable=True)
    electricity_cost = Column(Float, nullable=True)
    total_cost_per_12000_miles = Column(Float, nullable=True)
    euro_standard = Column(String, nullable=True)
    noise_level_dB_a_ = Column(Float, nullable=True)
    emissions_co_mg_per_km = Column(Float, nullable=True)
    thc_emissions_mg_per_km = Column(Float, nullable=True)
    emissions_nox_mg_per_km = Column(Float, nullable=True)
    thc_plus_nox_emissions_mg_per_km = Column(Float, nullable=True)
    particulates_no_mg_per_km = Column(Float, nullable=True)
    rde_nox_urban = Column(Float, nullable=True)
    rde_nox_combined = Column(Float, nullable=True)
    date_of_change = Column(Date, nullable=False)
    wiki_hashes = Column(ARRAY(CHAR(length=32)), nullable=True)
    year = Column(Integer, nullable=True)


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
