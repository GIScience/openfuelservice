from typing import Any, Union

import numpy as np
from sqlalchemy import Column
from tqdm import tqdm

from openfuelservice.server.db_import.models import EnvirocarSensorStatisticModel, CarfuelDataCarModel
from openfuelservice.server.statistics.objects import MatchedWikiECObject, AverageEnviroCarCategoryStatisticObject, \
    AverageCFDCategoryStatisticObject, MatchedWikiCFDObject
from openfuelservice.server.utils.database.queries import Misc, Envirocar, CarFuelData


class CFDAverageCategoryStatistics:
    def __init__(self):
        matched_cars = CarFuelData().get_cfd_data(ordered=True, with_wiki_hashes_only=True)
        self.ordered_cars = self.order_cars(matched_cars=matched_cars)
        print("")
        # Calculate per category per year

    def order_cars(self, matched_cars):
        # TODO finish statistics
        ordered_matched_cars_return = dict()
        for manufacturer in matched_cars:
            matched_car: CarfuelDataCarModel
            for matched_car in matched_cars[manufacturer]:
                matched_car_object = MatchedWikiCFDObject(matched_car=matched_car)
                year  = str(matched_car.year)
                fuel_type = matched_car.fuel_type
                categories_short_eu = matched_car_object.categories_short_eu
                for category_short_eu in categories_short_eu:
                    if category_short_eu not in ordered_matched_cars_return:
                        ordered_matched_cars_return[category_short_eu] = dict()
                    if year not in ordered_matched_cars_return[category_short_eu]:
                        ordered_matched_cars_return[category_short_eu][year] = dict()
                    if fuel_type not in ordered_matched_cars_return[category_short_eu][year]:
                        ordered_matched_cars_return[category_short_eu][year][fuel_type] = []
                    ordered_matched_cars_return[category_short_eu][year][fuel_type].append(matched_car)
        return ordered_matched_cars_return

    def calculate(self):
        av_cat_statistics = []
        for category in tqdm(self.ordered_cars, total=len(self.ordered_cars),
                             unit=' Calculating CFD Category Statistics'):
            for year in self.ordered_cars[category]:
                for fuel_type in self.ordered_cars[category][year]:
                    temp_value_holder: dict(map=[str, dict()]) = dict()
                    temp_value_holder['e_consumption_miles_per_kWh']: [] = []
                    temp_value_holder['e_consumption_wh_per_km']: [] = []
                    temp_value_holder['maximum_range_km']: [] = []
                    temp_value_holder['maximum_range_miles']: [] = []
                    temp_value_holder['metric_urban_cold']: [] = []
                    temp_value_holder['metric_extra_urban']: [] = []
                    temp_value_holder['metric_combined']: [] = []
                    temp_value_holder['co2_g_per_km']: [] = []
                    temp_value_holder['noise_level_dB_a_']: [] = []
                    temp_value_holder['emissions_co_mg_per_km']: [] = []
                    temp_value_holder['thc_emissions_mg_per_km']: [] = []
                    temp_value_holder['emissions_nox_mg_per_km']: [] = []
                    temp_value_holder['thc_plus_nox_emissions_mg_per_km']: [] = []
                    temp_value_holder['particulates_no_mg_per_km']: [] = []
                    temp_value_holder['rde_nox_urban']: [] = []
                    temp_value_holder['rde_nox_combined']: [] = []
                    cfd_car: MatchedWikiCFDObject
                    for cfd_car in self.ordered_cars[category][year][fuel_type]:
                        temp_value_holder['e_consumption_miles_per_kWh'].append(cfd_car.e_consumption_miles_per_kWh) if cfd_car.e_consumption_miles_per_kWh is not None else 0
                        temp_value_holder['e_consumption_wh_per_km'].append(cfd_car.e_consumption_wh_per_km) if cfd_car.e_consumption_wh_per_km is not None else 0
                        temp_value_holder['maximum_range_km'].append(cfd_car.maximum_range_km) if cfd_car.maximum_range_km is not None else 0
                        temp_value_holder['maximum_range_miles'].append(cfd_car.maximum_range_miles) if cfd_car.maximum_range_miles is not None else 0
                        temp_value_holder['metric_urban_cold'].append(cfd_car.metric_urban_cold) if cfd_car.metric_urban_cold is not None else 0
                        temp_value_holder['metric_extra_urban'].append(cfd_car.metric_extra_urban) if cfd_car.metric_extra_urban is not None else 0
                        temp_value_holder['metric_combined'].append(cfd_car.metric_combined) if cfd_car.metric_combined is not None else 0
                        temp_value_holder['co2_g_per_km'].append(cfd_car.co2_g_per_km) if cfd_car.co2_g_per_km is not None else 0
                        temp_value_holder['noise_level_dB_a_'].append(cfd_car.noise_level_dB_a_) if cfd_car.noise_level_dB_a_ is not None else 0
                        temp_value_holder['emissions_co_mg_per_km'].append(cfd_car.emissions_co_mg_per_km) if cfd_car.emissions_co_mg_per_km is not None else 0
                        temp_value_holder['thc_emissions_mg_per_km'].append(cfd_car.thc_emissions_mg_per_km) if cfd_car.thc_emissions_mg_per_km is not None else 0
                        temp_value_holder['emissions_nox_mg_per_km'].append(cfd_car.emissions_nox_mg_per_km) if cfd_car.emissions_nox_mg_per_km is not None else 0
                        temp_value_holder['thc_plus_nox_emissions_mg_per_km'].append(cfd_car.thc_plus_nox_emissions_mg_per_km) if cfd_car.thc_plus_nox_emissions_mg_per_km is not None else 0
                        temp_value_holder['particulates_no_mg_per_km'].append(cfd_car.particulates_no_mg_per_km) if cfd_car.particulates_no_mg_per_km is not None else 0
                        temp_value_holder['rde_nox_urban'].append(cfd_car.rde_nox_urban) if cfd_car.rde_nox_urban is not None else 0
                        temp_value_holder['rde_nox_combined'].append(cfd_car.rde_nox_combined) if cfd_car.rde_nox_combined is not None else 0

                    for phenomenon in temp_value_holder:
                        values = temp_value_holder[phenomenon]
                        values = [value for value in values if value is not None and value > 0]
                        value_length = len(values)
                        values_sum = sum(values)
                        if value_length > 0:
                            av_cat_statistics.append(AverageCFDCategoryStatisticObject(
                                phenomenon=phenomenon,
                                category_short_eu=category,
                                vehicle_type='car',
                                fuel_type=fuel_type,
                                value=values_sum/value_length,
                                numb_cars=value_length,
                                year=str(year)
                            ))
        return av_cat_statistics


class EnvirocarAverageCategoryStatistics:
    def __init__(self):
        matched_cars = Envirocar().get_sensors(with_wiki_hashes_only=True)
        self.matched_ordered_car_objects = self.order_matched_cars(matched_cars=matched_cars)

    def order_matched_cars(self, matched_cars: []):
        ordered_matched_cars_return = dict()
        matched_with_stats = 0
        matched_without_stats = 0
        for matched_car in matched_cars:
            matched_car_object = MatchedWikiECObject(
                matched_car=matched_car
            )
            if len(matched_car_object.sensor_statistics) > 0:
                matched_with_stats += 1
                categories_short_eu: [] = matched_car_object.categories_short_eu
                fuel_type: str = matched_car_object.fuel_type
                sensor_id: str = matched_car_object.sensor_id
                category_short_eu: str
                for category_short_eu in categories_short_eu:
                    if category_short_eu not in ordered_matched_cars_return:
                        ordered_matched_cars_return[category_short_eu] = dict()
                    if fuel_type not in ordered_matched_cars_return[category_short_eu]:
                        ordered_matched_cars_return[category_short_eu][fuel_type] = dict()
                    if sensor_id not in ordered_matched_cars_return[category_short_eu][fuel_type]:
                        ordered_matched_cars_return[category_short_eu][fuel_type][sensor_id] = matched_car_object
                    else:
                        pass
            else:
                matched_without_stats += 1
        print(
            "Total matched Car objects with stats: {} | Without Stats: {}".format(matched_with_stats, matched_without_stats))
        return ordered_matched_cars_return

    def calculate(self) -> []:
        av_cat_statistics = []
        for category in tqdm(self.matched_ordered_car_objects, total=len(self.matched_ordered_car_objects),
                             unit=' Calculating Category Statistics'):
            for fuel_type in self.matched_ordered_car_objects[category]:
                temp_value_holder: dict(map=[str, dict()]) = dict()
                for sensor in self.matched_ordered_car_objects[category][fuel_type]:
                    sensor_object: MatchedWikiECObject = self.matched_ordered_car_objects[category][fuel_type][sensor]
                    sensor_statistics: [] = sensor_object.sensor_statistics
                    for sensor_statistic in sensor_statistics:
                        sensor_statistic: EnvirocarSensorStatisticModel
                        phenomenon: str = sensor_statistic.phenomenon_name
                        max = float(sensor_statistic.max)
                        average = float(sensor_statistic.avg)
                        min = float(sensor_statistic.min)
                        phenomenon_weights = sensor_statistic.numb_measurements
                        sensor_id = sensor_statistic.sensor_id
                        if phenomenon == 'CO2' and min < 0:
                            min = 0
                        if phenomenon == 'Speed' and min < 0:
                            min = 0
                        if phenomenon not in temp_value_holder:
                            temp_value_holder[phenomenon]: dict(map=[str, []]) = dict()
                            temp_value_holder[phenomenon]['max']: [] = []
                            temp_value_holder[phenomenon]['average']: [] = []
                            temp_value_holder[phenomenon]['min']: [] = []
                            temp_value_holder[phenomenon]['phenomenon_weights']: [] = []
                            temp_value_holder[phenomenon]['sensors']: [] = []
                            temp_value_holder[phenomenon]['fuel_type']: str = fuel_type
                            temp_value_holder[phenomenon]['vehicle_type']: str = sensor_object.vehicle_type
                            temp_value_holder[phenomenon]['category_short_eu']: str = category
                        temp_value_holder[phenomenon]['max'].append(max)
                        temp_value_holder[phenomenon]['average'].append(average)
                        temp_value_holder[phenomenon]['min'].append(min)
                        temp_value_holder[phenomenon]['phenomenon_weights'].append(phenomenon_weights)
                        temp_value_holder[phenomenon]['sensors'].append(sensor_id)
                for phenomenon in temp_value_holder:
                    phenomenon_weights = temp_value_holder[phenomenon]['phenomenon_weights']
                    measurements = sum(phenomenon_weights)
                    numb_sensors = len(temp_value_holder[phenomenon]['sensors'])
                    max = temp_value_holder[phenomenon]['max']
                    average = temp_value_holder[phenomenon]['average']
                    min = temp_value_holder[phenomenon]['min']
                    min_average = np.average(min, weights=phenomenon_weights)
                    av_cat_statistics.append(AverageEnviroCarCategoryStatisticObject(
                        category_short_eu=temp_value_holder[phenomenon]['category_short_eu'],
                        vehicle_type=temp_value_holder[phenomenon]['vehicle_type'],
                        fuel_type=temp_value_holder[phenomenon]['fuel_type'],
                        phenomenon=phenomenon,
                        max=np.average(max, weights=phenomenon_weights),
                        average=np.average(average, weights=phenomenon_weights),
                        min=min_average if float(min_average) > 0 else 0,
                        measurements=measurements,
                        numb_sensors=numb_sensors
                    ))
        return av_cat_statistics
