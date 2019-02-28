from openfuelservice.server.db_import.models import MatchedWikiEnvirocarModel, EnvirocarSensorModel, WikiCarModel, \
    CarfuelDataCarModel
from openfuelservice.server.utils.database.queries import Wikipedia


class MatchedWikiCFDObject(object):
    def __init__(self, matched_car: CarfuelDataCarModel):
        self.matched_car: CarfuelDataCarModel = matched_car
        self.hash: str = matched_car.hash_id
        self.manufacturer = matched_car.manufacturer
        self.model = matched_car.model
        self.description = matched_car.description
        self.transmission = matched_car.transmission
        self.engine_capacity = matched_car.engine_capacity
        self.fuel_type = matched_car.fuel_type
        self.e_consumption_miles_per_kWh = matched_car.e_consumption_miles_per_kWh
        self.e_consumption_wh_per_km = matched_car.e_consumption_wh_per_km
        self.maximum_range_km = matched_car.maximum_range_km
        self.maximum_range_miles = matched_car.maximum_range_miles
        self.metric_urban_cold = matched_car.metric_urban_cold
        self.metric_extra_urban = matched_car.metric_extra_urban
        self.metric_combined = matched_car.metric_combined
        self.imperial_urban_cold = matched_car.imperial_urban_cold
        self.imperial_extra_urban = matched_car.imperial_extra_urban
        self.imperial_combined = matched_car.imperial_combined
        self.co2_g_per_km = matched_car.co2_g_per_km
        self.fuel_cost_6000_miles = matched_car.fuel_cost_6000_miles
        self.fuel_cost_12000_miles = matched_car.fuel_cost_12000_miles
        self.electricity_cost = matched_car.electricity_cost
        self.total_cost_per_12000_miles = matched_car.total_cost_per_12000_miles
        self.euro_standard = matched_car.euro_standard
        self.noise_level_dB_a_ = matched_car.noise_level_dB_a_
        self.emissions_co_mg_per_km = matched_car.emissions_co_mg_per_km
        self.thc_emissions_mg_per_km = matched_car.thc_emissions_mg_per_km
        self.emissions_nox_mg_per_km = matched_car.emissions_nox_mg_per_km
        self.thc_plus_nox_emissions_mg_per_km = matched_car.thc_plus_nox_emissions_mg_per_km
        self.particulates_no_mg_per_km = matched_car.particulates_no_mg_per_km
        self.rde_nox_urban = matched_car.rde_nox_urban
        self.rde_nox_combined = matched_car.rde_nox_combined
        self.date_of_change = matched_car.date_of_change
        self.wiki_hashes = matched_car.wiki_hashes
        self.year = matched_car.year
        self.wiki_car_objects: [WikiCarModel]
        wiki_car_objects = Wikipedia().get_cars_by_hashes(self.wiki_hashes)
        self.categories_short_eu: [] = []
        [self.categories_short_eu.append(wiki_car_object.category_short_eu) for wiki_car_object in wiki_car_objects if
         type(wiki_car_object) == WikiCarModel]


class MatchedWikiECObject(object):
    def __init__(self, matched_car: EnvirocarSensorModel):
        self.matched_car: EnvirocarSensorModel = matched_car
        self.sensor_id: str = matched_car.sensor_id
        self.wiki_hashes: [] = matched_car.wiki_hashes
        self.fuel_type = matched_car.fuel_type
        self.sensor_statistics = matched_car.sensors_statistics.all()
        self.vehicle_type = matched_car.sensor_type
        wiki_car_objects: [WikiCarModel]
        wiki_car_objects = Wikipedia().get_cars_by_hashes(self.wiki_hashes)
        self.categories_short_eu: [] = []
        [self.categories_short_eu.append(wiki_car_object.category_short_eu) for wiki_car_object in wiki_car_objects if
         type(wiki_car_object) == WikiCarModel]


class AverageEnviroCarCategoryStatisticObject(object):
    def __init__(self, category_short_eu, vehicle_type, fuel_type, phenomenon, max, average, min, measurements,
                 numb_sensors):
        self.category_short_eu = category_short_eu
        self.vehicle_type = vehicle_type
        self.fuel_type = fuel_type
        self.phenomenon = phenomenon
        self.max = max
        self.average = average
        self.min = min
        self.measurements = measurements
        self.numb_sensors = numb_sensors


class AverageCFDCategoryStatisticObject(object):
    def __init__(self, phenomenon, category_short_eu, vehicle_type, fuel_type, value, numb_cars, year):
        self.phenomenon = phenomenon
        self.category_short_eu = category_short_eu
        self.vehicle_type = vehicle_type
        self.fuel_type = fuel_type
        self.value = value
        self.numb_cars = numb_cars
        self.year = year


class AverageEnviroCarVehicleTypeStatisticObject(object):
    def __init__(self, vehicle_type, fuel_type, phenomenon, max, average, min, measurements, numb_sensors):
        self.vehicle_type = vehicle_type
        self.fuel_type = fuel_type
        self.phenomenon = phenomenon
        self.max = max
        self.average = average
        self.min = min
        self.measurements = measurements
        self.numb_sensors = numb_sensors


class AverageEnviroCarManufacturerStatisticObject(object):
    def __init__(self, manufacturer, vehicle_type, fuel_type, phenomenon, max, average, min, measurements,
                 numb_sensors):
        self.manufacturer = manufacturer
        self.vehicle_type = vehicle_type
        self.fuel_type = fuel_type
        self.phenomenon = phenomenon
        self.max = max
        self.average = average
        self.min = min
        self.measurements = measurements
        self.numb_sensors = numb_sensors
