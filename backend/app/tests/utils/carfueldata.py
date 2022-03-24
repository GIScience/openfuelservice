# import datetime
# import random
# from enum import Enum
# from typing import Dict
#
# from sqlalchemy.orm import Session
#
# from app import crud, models
# from app.schemas.carfueldata_car import CarfueldataCarCreate
# from app.schemas.track import TrackCreate
# from app.schemas.track_measurement import TrackMeasurementCreate
# from app.utils import get_random_string
#
#
# class FuelType(tuple, Enum):
#     DIESEL: tuple = ("Diesel", "Internal Combustion Engine (ICE)")
#     PETROL: tuple = ("Petrol", "Internal Combustion Engine (ICE)")
#     HYBRID: tuple = ("Electricity / Petrol", "Plug-in Hybrid Electric Vehicle (PHEV)")
#     ELECTRIC: tuple = ("Electricity", "Battery Electric Vehicle (BEV) / Pure Electric Vehicle / Electric Vehicle (EV)")
#
#
# def create_random_carfueldata_car(
#         db: Session,
#         fuel_type: FuelType = FuelType.PETROL,
# ) -> models.EnvirocarSensor:
#     unique_number = random.randint(1000, 9999)
#     unique_model = get_random_string(10)
#     unique_manufacturer = get_random_string(10)
#     test1 = fuel_type.value[0]
#     test2 = fuel_type.value[1]
#     carfueldata_car_in = CarfueldataCarCreate(
#         id=unique_number,
#         manufacturer="Ford",
#         model=get_random_string(5),
#         description=get_random_string(5),
#         transmission=get_random_string(3),
#         engine_capacity=0 if fuel_type == FuelType.ELECTRIC else 1368,
#         fuel_type=fuel_type.value[0],
#         electric_energy_consumption_miles_kwh=0 if fuel_type == FuelType.PETROL or fuel_type == FuelType.DIESEL else
#         random.uniform(
#             2.0, 10.0),
#         manual_or_automatic=random.choice(['manual', 'automatic']),
#         powertrain=fuel_type.value[1],
#         engine_power_ps=random.randint(165, 500),
#         engine_power_kw=,
#         wh_km=,
#         maximum_range_km=,
#         maximum_range_miles=,
#         euro_standard=,
#         diesel_ved_supplement=,
#         testing_scheme=,
#         wltp_imperial_low=,
#         wltp_imperial_medium=,
#         wltp_imperial_high=,
#         wltp_imperial_extra_high=,
#         wltp_imperial_combined=,
#         wltp_imperial_combined_weighted=,
#         wltp_metric_low=,
#         wltp_metric_medium=,
#         wltp_metric_high=,
#         wltp_metric_extra_high=,
#         wltp_metric_combined=,
#         wltp_metric_combined_weighted=,
#         wltp_co2=,
#         wltp_co2_weighted=,
#         equivalent_all_electric_range_miles=,
#         equivalent_all_electric_range_km=,
#         electric_range_city_miles=,
#         electric_range_city_km=,
#         emissions_co_mg_km=,
#         thc_emissions_mg_km=,
#         emissions_nox_mg_km=,
#         thc_nox_emissions_mg_km=,
#         particulates_no_mg_km=,
#         rde_nox_urban=,
#         rde_nox_combined=,
#         noise_level_dba=,
#         wiki_hashes=,
#         date_of_change=,
#         year=,
#     )
#     return crud.carfueldata_car.create(db=db, obj_in=carfueldata_car_in)
