# import json
#
# import numpy as np
# from flask import request
#
# from openfuelservice.server import file_folder, temp_folder
# from openfuelservice.server.base_calculations.queries import query_countries_w_prices, \
#     query_cfd_average_category_statistics, query_ec_average_category_statistics
# from openfuelservice.server.db_import.models import CarfuelDataCarModel, EnvirocarAverageCategoryStatisticsModel, \
#     EnvirocarSensorModel, WikiCarModel, EnvirocarSensorStatisticModel
# from openfuelservice.server.drivers.carfueldata_driver import LatestCars
# from openfuelservice.server.drivers.envirocar_driver import ECData
# from openfuelservice.server.statistics import client, logger
# from openfuelservice.server.utils.database.queries import CarFuelData, Envirocar, Wikipedia
# from openfuelservice.server.utils.misc import file_management
# from openfuelservice.server.utils.misc.geometries import truncate
#
#
# def get_ec_data():
#     # Clean old files
#     cfd_route_data = CFDConsumption()
#     cfd_route_data = CFDConsumption().calculate_stepping_per_class(10, 180)
#     file_management.create_directory(temp_folder)
#     file_management.clean_directory(temp_folder)
#     # Get Data
#     price_avail_country = ESDataDB().price_availability_countries()
#     ec_data_db = ECDataDB()
#     average_consumption = ec_data_db.average_car_data()
#     average_co2 = ec_data_db.average_co2()
#
#     ec_matched_cars = ec_data_db.numb_matched_cars()
#     print("EC: Matched cars: " + str(ec_matched_cars))
#     ec_unmatched_cars = ec_data_db.numb_unmatched_cars()
#     print("EC: Unmatched cars: " + str(ec_unmatched_cars))
#     ec_unique_matched_cars = ec_data_db.numb_unique_matched_cars()
#     print("EC: Aggregated cars: " + str(ec_unique_matched_cars))
#     ec_carstats_per_class = ec_data_db.cars_per_class()
#     ec_carstats_per_brand = ec_data_db.cars_per_brand()
#
#     ec_data_api = ECDataAPI()
#     ec_api_filter_stats = dict()
#     ec_api_filter_stats['raw_cars'] = ec_data_api.numb_all_cars_noname() + ec_data_api.numb_all_cars_right_name()
#     ec_api_filter_stats['1st_filter'] = ec_data_api.numb_all_cars_noname()
#     ec_api_filter_stats['2nd_filter'] = ec_data_api.numb_all_cars_right_name() - ec_data_api.numb_all_cars_stats()
#     ec_api_filter_stats['3rd_filter'] = ec_data_api.numb_all_cars_stats() - ec_data_api.numb_cars_usable_stats()
#     ec_api_filter_stats['final_cars'] = ec_api_filter_stats['raw_cars'] - ec_api_filter_stats['1st_filter'] - \
#                                         ec_api_filter_stats['1st_filter'] - ec_api_filter_stats['2nd_filter'] - \
#                                         ec_api_filter_stats['3rd_filter']
#
#     cfd_data_db = CFDDataDB()
#     # cfd_number_api_cars = CFDDataAPI().numb_cars()
#     # cfd_matched_cars = cfd_data_db.numb_matched_cars()
#     # cfd_unmatched_cars = cfd_data_db.numb_unmatched_cars()
#     # cfd_unique_matched_cars = cfd_data_db.numb_unique_matched_cars()
#     cfd_carstats_per_class = cfd_data_db.cars_per_class()
#     matching_comparison = Comparisons().compare_matched_unmatched_cfd_ec()
#
#     # Open Files
#     es_availability_csv = temp_folder.joinpath('es_availability_country.csv').open(mode='w+')
#     ec_categories_csv = temp_folder.joinpath('ec_cars_per_category.csv').open(mode='w+')
#     ec_brands_csv = temp_folder.joinpath('ec_cars_per_brand.csv').open(mode='w+')
#     ec_api_filter_stats_csv = temp_folder.joinpath('ec_api_filter_stats.csv').open(mode='w+')
#     cfd_categories_csv = temp_folder.joinpath('cfd_cars_per_category.csv').open(mode='w+')
#     matching_comparison_csv = temp_folder.joinpath('matching_comparison.csv').open(mode='w+')
#     consumption_100km = temp_folder.joinpath('consumption_100km.csv').open(mode='w+')
#     route_data_100km_csv = temp_folder.joinpath('route_data_100km.csv').open(mode='w+')
#     nox_100km = temp_folder.joinpath('nox_100km.csv').open(mode='w+')
#     thc_100km = temp_folder.joinpath('thc_100km.csv').open(mode='w+')
#
#     # Create Headers
#     es_availability_header = "ISO2, year_availability\n"
#     ec_categories_header = "category, category_cars, combined_cars, category_diesel_cars, category_gasoline_cars, brand_counter, measurements\n"
#     cfd_categories_header = "category, category_cars, combined_cars, category_diesel_cars, category_gasoline_cars, brand_counter\n"
#     ec_brands_header = "brand, brand_cars, brand_diesel_cars, brand_gasoline_cars, categories\n"
#     matching_comparison_header = "ec, cfd\n"
#     ec_api_filter_stats_header = "Ungefiltert, 1. Filter, 2. Filter, 3. Filter, Final\n"
#     consumption_100km_header = "Geschwindigkeit, a, b, c, d, "
#     route_data_100km_header = "Klasse, 30, 60, 90, 120, 150, 180"
#     nox_100km_header = "Klasse, 30, 60, 90, 120, 150, 180"
#     thc_100km_header = "Klasse, 30, 60, 90, 120, 150, 180"
#
#     # Write Headers
#     es_availability_csv.write(es_availability_header)
#     ec_categories_csv.write(ec_categories_header)
#     ec_api_filter_stats_csv.write(ec_api_filter_stats_header)
#     cfd_categories_csv.write(cfd_categories_header)
#     ec_brands_csv.write(ec_brands_header)
#     matching_comparison_csv.write(matching_comparison_header)
#     route_data_100km_csv.write(route_data_100km_header)
#     # consumption_100km.write(consumption_100km_header)
#     # nox_100km.write(nox_100km_header)
#     # thc_100km.write(thc_100km_header)  ###
#
#     # Write to Files
#     for category in cfd_route_data:
#         category_data = cfd_route_data[category]
#         row = category + ","
#         for speed in category_data:
#             speed_data = category_data[speed]
#             consumption = str(truncate(speed_data['consumption'], 2))
#             co2 = str(truncate(speed_data['co2'], 2)) if 'co2' in speed_data else "nan"
#             co = str(truncate(speed_data['co'], 2)) if 'co' in speed_data else "nan"
#             nox = str(truncate(speed_data['nox'], 2)) if 'nox' in speed_data else "nan"
#             thc = str(truncate(speed_data['thc'], 2)) if 'thc' in speed_data else "nan"
#             cost = str(truncate(speed_data['cost'], 2)) if 'cost' in speed_data else "nan"
#             row += ("(" + consumption + "/" + co2 + "/" + co + "/" + nox + "/" + thc + "/" + cost + ")" + ",")
#         row += "\n"
#         route_data_100km_csv.write(row)
#
#     matched_comparison_row = str(matching_comparison['ec_matched']) + "," + str(
#         matching_comparison['cfd_matched']) + "\n"
#     unmatched_comparison_row = str(matching_comparison['ec_unmatched']) + "," + str(
#         matching_comparison['cfd_unmatched']) + "\n"
#     matching_comparison_csv.write(matched_comparison_row)
#     matching_comparison_csv.write(unmatched_comparison_row)
#
#     ec_api_filter_stats_csv.write(
#         str(ec_api_filter_stats['raw_cars']) + "," + str(ec_api_filter_stats['1st_filter']) + "," + str(
#             ec_api_filter_stats['2nd_filter']) + "," + str(ec_api_filter_stats['3rd_filter']) + "," + str(
#             ec_api_filter_stats['final_cars']))
#
#     for country in price_avail_country:
#         row = country + "," + str(price_avail_country[country]) + "\n"
#         es_availability_csv.write(row)
#     for category in cfd_carstats_per_class:
#         category_cars = cfd_carstats_per_class[category]['car_counter']
#         category_diesel_cars = cfd_carstats_per_class[category]['diesel_counter'] if 'diesel_counter' in \
#                                                                                      cfd_carstats_per_class[
#                                                                                          category] else 0
#         category_gasoline_cars = cfd_carstats_per_class[category]['gasoline_counter'] if 'gasoline_counter' in \
#                                                                                          cfd_carstats_per_class[
#                                                                                              category] else 0
#         individual_cars = cfd_carstats_per_class[category]['individual_cars']
#         brands = cfd_carstats_per_class[category]['brand_counter']
#         row = category + "," + str(category_cars) + "," + str(individual_cars) + "," + str(
#             category_diesel_cars) + "," + str(
#             category_gasoline_cars) + "," + str(brands) + "\n"
#         cfd_categories_csv.write(row)
#     for category in ec_carstats_per_class:
#         category_cars = ec_carstats_per_class[category]['car_counter']
#         category_diesel_cars = ec_carstats_per_class[category]['diesel_counter'] if 'diesel_counter' in \
#                                                                                     ec_carstats_per_class[
#                                                                                         category] else 0
#         category_gasoline_cars = ec_carstats_per_class[category]['gasoline_counter'] if 'gasoline_counter' in \
#                                                                                         ec_carstats_per_class[
#                                                                                             category] else 0
#         individual_cars = ec_carstats_per_class[category]['individual_cars']
#         brands = ec_carstats_per_class[category]['brand_counter']
#         measurements = ec_carstats_per_class[category]['measurements'] if 'measurements' in ec_carstats_per_class[
#             category] else 0
#         row = category + "," + str(category_cars) + "," + str(individual_cars) + "," + str(
#             category_diesel_cars) + "," + str(
#             category_gasoline_cars) + "," + str(brands) + "," + str(measurements) + "\n"
#         ec_categories_csv.write(row)
#     for brand in ec_carstats_per_brand:
#         brand_data = ec_carstats_per_brand[brand]
#         brand_cars = brand_data['car_counter']
#         brand_diesel_cars = brand_data['diesel_counter'] if 'diesel_counter' in brand_data else 0
#         brand_gasoline_cars = brand_data['gasoline_counter'] if 'gasoline_counter' in brand_data else 0
#         categories = ' '.join(str(e) for e in brand_data['categories']) if 'categories' in brand_data else ''
#         row = brand + "," + str(brand_cars) + "," + str(brand_diesel_cars) + "," + str(
#             brand_gasoline_cars) + "," + categories + "\n"
#         ec_brands_csv.write(row)
#     # Close Files
#     es_availability_csv.close()
#     ec_categories_csv.close()
#     ec_brands_csv.close()
#     cfd_categories_csv.close()
#     matching_comparison_csv.close()
#     ec_api_filter_stats_csv.close()
#     route_data_100km_csv.close()
#
#
# class Comparisons:
#
#     def __init__(self):
#         self.ec_all_cars = Envirocar().get_sensors(with_wiki_hashes_only=False)
#         self.ec_matched_cars = Envirocar().get_sensors(with_wiki_hashes_only=True)
#         self.cfd_all_cars = CarFuelData().get_cfd_data(with_wiki_hashes_only=False)
#         self.cfd_matched_cars = CarFuelData().get_cfd_data(with_wiki_hashes_only=True)
#
#     def compare_matched_unmatched_cfd_ec(self):
#         logger.info("EC-CFD: Constructing comparison stats")
#         matching_comparison = dict()
#         matching_comparison['ec_matched'] = len(self.ec_matched_cars)
#         matching_comparison['cfd_matched'] = len(self.cfd_matched_cars)
#         matching_comparison['ec_unmatched'] = len(self.ec_all_cars) - len(self.ec_matched_cars)
#         matching_comparison['cfd_unmatched'] = len(self.cfd_all_cars) - len(self.cfd_matched_cars)
#         return matching_comparison
#
#
# class ECDataDB:
#     ec_machted_cars = None
#     diesel_average_data = None
#     gasoline_average_data = None
#
#     def __init__(self):
#         self.ec_machted_cars = Envirocar().get_sensors(with_wiki_hashes_only=True)
#         self.ec_all_cars = Envirocar().get_sensors(with_wiki_hashes_only=False)
#         self.diesel_average_data = query_ec_average_category_statistics('diesel')
#         self.gasoline_average_data = query_ec_average_category_statistics('gasoline')
#
#     def numb_unmatched_cars(self):
#         return len(self.ec_all_cars) - len(self.ec_machted_cars)
#
#     def numb_matched_cars(self):
#         return len(self.ec_machted_cars)
#
#     def numb_unique_matched_cars(self):
#         already_counted = list()
#         unique_matched_cars = 0
#         car: EnvirocarSensorModel
#         for car in self.ec_machted_cars:
#             wiki_hashes = car.wiki_hashes
#             if wiki_hashes not in already_counted:
#                 already_counted.append(wiki_hashes)
#                 unique_matched_cars += 1
#         return unique_matched_cars
#
#     def numb_cars_per_classes(self):
#         cars_per_category = dict()
#         data: EnvirocarAverageCategoryStatisticsModel
#         for data in self.diesel_average_data:
#             category = data.category_short_eu
#             numb_cars = data.numb_sensors
#             fuel_type = data.fuel_type
#             if category not in cars_per_category:
#                 cars_per_category[category] = dict()
#                 cars_per_category[category][fuel_type] = numb_cars
#             elif category in cars_per_category and fuel_type not in cars_per_category[category]:
#                 cars_per_category[category][fuel_type] = numb_cars
#             else:
#                 cars_per_category[category][fuel_type] += numb_cars
#         for data in self.gasoline_average_data:
#             category = data.category_short_eu
#             numb_cars = data.numb_sensors
#             fuel_type = data.fuel_type
#             if category not in cars_per_category:
#                 cars_per_category[category] = dict()
#                 cars_per_category[category][fuel_type] = numb_cars
#             elif category in cars_per_category and fuel_type not in cars_per_category[category]:
#                 cars_per_category[category][fuel_type] = numb_cars
#             else:
#                 cars_per_category[category][fuel_type] += numb_cars
#         return cars_per_category
#
#     def cars_per_class(self):
#         logger.info("EC: Constructing cars per class stats")
#         cars_per_category = dict()
#         processed_brands = dict()
#         processed_cars = dict()
#         processed_wiki_cars = dict()
#         car: EnvirocarSensorModel
#         for car in self.ec_machted_cars:
#             wiki_hashes = car.wiki_hashes
#             wiki_cars = Wikipedia().get_cars_by_hashes(wiki_hashes)
#             fuel_type = car.fuel_type
#             brand_name = car.car_manufacturer
#             measurements: EnvirocarSensorStatisticModel = Envirocar().get_sensor_stats(sensor_id=car.sensor_id,
#                                                                                        first_only=True)
#             sensor_id = car.sensor_id
#             wiki_car: WikiCarModel
#             for wiki_car in wiki_cars:
#                 category = wiki_car.category_short_eu
#                 wiki_car_brand = wiki_car.brand_name
#                 wiki_car_name = wiki_car_brand + wiki_car.car_name
#                 if category not in cars_per_category:
#                     cars_per_category[category] = dict()
#                     processed_brands[category] = list()
#                     processed_cars[category] = list()
#                     processed_wiki_cars[category] = list()
#                     cars_per_category[category]['car_counter'] = 0
#                     cars_per_category[category]['brand_counter'] = 0
#                     cars_per_category[category]['individual_cars'] = 0
#                     cars_per_category[category]['measurements'] = 0
#                     cars_per_category[category]['{}_counter'.format(fuel_type)] = 0
#                 if '{}_counter'.format(fuel_type) not in cars_per_category[category]:
#                     cars_per_category[category]['{}_counter'.format(fuel_type)] = 0
#                 if sensor_id not in processed_cars[category]:
#                     if brand_name not in processed_brands[category]:
#                         cars_per_category[category]['brand_counter'] += 1
#                         processed_brands[category].append(brand_name)
#                     if wiki_car_name not in processed_cars[category]:
#                         cars_per_category[category]['individual_cars'] += 1
#                         processed_cars[category].append(wiki_car_name)
#
#                     if measurements is not None:
#                         cars_per_category[category]['measurements'] += measurements.numb_measurements
#                     cars_per_category[category]['car_counter'] += 1
#                     cars_per_category[category]['{}_counter'.format(fuel_type)] += 1
#                     processed_cars[category].append(sensor_id)
#
#         return cars_per_category
#
#     def cars_per_brand(self):
#         logger.info("EC: Constructing cars per brand stats")
#         cars_per_brand = dict()
#         car: EnvirocarSensorModel
#         for car in self.ec_machted_cars:
#             wiki_hashes = car.wiki_hashes
#             wiki_cars = Wikipedia().get_cars_by_hashes(wiki_hashes)
#             car_brand = car.car_manufacturer
#             fuel_type = car.fuel_type
#             wiki_car: WikiCarModel
#             for wiki_car in wiki_cars:
#                 category = wiki_car.category_short_eu
#                 if car_brand not in cars_per_brand:
#                     cars_per_brand[car_brand] = dict()
#                     cars_per_brand[car_brand]['categories'] = list()
#                     cars_per_brand[car_brand]['car_counter'] = 0
#                 if '{}_counter'.format(fuel_type) not in cars_per_brand[car_brand]:
#                     cars_per_brand[car_brand]['{}_counter'.format(fuel_type)] = 0
#                 if category not in cars_per_brand[car_brand]['categories']:
#                     cars_per_brand[car_brand]['categories'].append(category)
#                 cars_per_brand[car_brand]['car_counter'] += 1
#                 cars_per_brand[car_brand]['{}_counter'.format(fuel_type)] += 1
#         return cars_per_brand
#
#     def average_car_data(self):
#         average_data = dict()
#         # consumption parameters
#         average_gasoline_consumption = []
#         average_gasoline_consumption_weights = []
#         average_diesel_consumption = []
#         average_diesel_consumption_weights = []
#         # co2 parameters
#         average_gasoline_co2 = []
#         average_gasoline_co2_weights = []
#         average_diesel_co2 = []
#         average_diesel_co2_weights = []
#
#         car: EnvirocarSensorModel
#         for car in self.ec_all_cars:
#             sensor_id = car.sensor_id
#             statistics = Envirocar().get_sensor_stats(sensor_id=sensor_id)
#             speed_min = 0
#             speed_avg = 0
#             speed_max = 0
#             statistic: EnvirocarSensorStatisticModel
#             for statistic in statistics:
#                 phenomenon = statistic.phenomenon_name
#                 if phenomenon.lower() == 'speed':
#                     speed_avg = float(statistic.avg)
#             for statistic in statistics:
#                 fuel_type = car.fuel_type
#                 phenomenon = statistic.phenomenon_name
#                 numb_measurements = float(statistic.numb_measurements)
#                 average = statistic.avg
#                 if 'consumption' in phenomenon.lower() and int(average) > 0:
#                     cons_avg = float(statistic.avg)
#                     cons_avg = cons_avg/speed_avg
#                     average = cons_avg * 100
#                     if fuel_type == 'gasoline':
#                         average_gasoline_consumption.append(average)
#                         average_gasoline_consumption_weights.append(numb_measurements)
#                     if fuel_type == 'diesel':
#                         average_diesel_consumption.append(average)
#                         average_diesel_consumption_weights.append(numb_measurements)
#                 if 'co2' in phenomenon.lower() and int(average) > 0:
#                     co2_avg = float(statistic.avg)
#                     co2_avg = co2_avg / speed_avg
#                     average = co2_avg * 1000
#                     if fuel_type == 'gasoline':
#                         average_gasoline_co2.append(average)
#                         average_gasoline_co2_weights.append(numb_measurements)
#                     if fuel_type == 'diesel':
#                         average_diesel_co2.append(average)
#                         average_diesel_co2_weights.append(numb_measurements)
#         average_data['gasoline_consumption_average'] = np.average(average_gasoline_consumption, weights=average_gasoline_consumption_weights)
#         average_data['diesel_consumption_average'] = np.average(average_diesel_consumption, weights=average_diesel_consumption_weights)
#         average_data['gasoline_co2_average'] = np.average(average_gasoline_co2, weights=average_gasoline_co2_weights)
#         average_data['diesel_co2_average'] = np.average(average_diesel_co2, weights=average_diesel_co2_weights)
#         print("Average Gasoline Consumption:" + str(round(average_data['gasoline_consumption_average'], 1)))
#         print("Average Diesel Consumption:" + str(round(average_data['diesel_consumption_average'], 1)))
#         print("Average Gasoline co2:" + str(round(average_data['gasoline_co2_average'], 1)))
#         print("Average Diesel co2:" + str(round(average_data['diesel_co2_average'], 1)))
#         return average_data
#
#     def average_co2(self):
#         pass
#
#
# class ECDataAPI:
#     envirocar_data = None
#
#     def __init__(self):
#         self.envirocar_data = ECData(all_parameters_min=True).get_data()
#
#     def numb_all_cars_right_name(self):
#         return len(self.envirocar_data.sensors)
#
#     def numb_all_cars_stats(self):
#         statistic_counter = 0
#         sensor_statistics = self.envirocar_data.sensors_statistics
#         for sensor in sensor_statistics:
#             if len(sensor_statistics[sensor]) > 0:
#                 statistic_counter += 1
#         return statistic_counter
#
#     def numb_all_cars_noname(self):
#         return 32
#
#     def numb_cars_usable_stats(self):
#         statistic_counter = 0
#         sensor_statistics = self.envirocar_data.sensors_statistics
#         for sensor in sensor_statistics:
#             statistics = sensor_statistics[sensor]
#             if 'Speed' in statistics and 'Consumption' in statistics:
#                 statistic_counter += 1
#         return statistic_counter
#
#
# class CFDDataAPI:
#     def numb_cars(self):
#         latest_carfueldata_cars = LatestCars().get_data()
#         numb_cars = len(latest_carfueldata_cars.cfd_objects_list)
#         return numb_cars
#
#
# class CFDDataDB:
#     cfd_matched_cars_db = None
#     diesel_average_data = None
#     gasoline_average_data = None
#
#     def __init__(self):
#         self.cfd_matched_cars_db = CarFuelData().get_cfd_data(with_wiki_hashes_only=True)
#         self.cfd_all_cars_db = CarFuelData().get_cfd_data(with_wiki_hashes_only=False)
#         self.diesel_average_data = query_cfd_average_category_statistics('diesel')
#         self.gasoline_average_data = query_cfd_average_category_statistics('gasoline')
#
#     def numb_unmatched_cars(self):
#         return len(self.cfd_all_cars_db) - len(self.cfd_matched_cars_db)
#
#     def numb_matched_cars(self):
#         return len(self.cfd_matched_cars_db)
#
#     def numb_unique_matched_cars(self):
#         already_counted = list()
#         unique_matched_cars = 0
#         car: CarfuelDataCarModel
#         for car in self.cfd_matched_cars_db:
#             wiki_hashes = car.wiki_hashes
#             if wiki_hashes not in already_counted:
#                 already_counted.append(wiki_hashes)
#                 unique_matched_cars += 1
#         return unique_matched_cars
#
#     def cars_per_class(self):
#         logger.info("CFD: Constructing cars per class stats")
#         cars_per_category = dict()
#         processed_brands = dict()
#         processed_cars = dict()
#         car: CarfuelDataCarModel
#         for car in self.cfd_all_cars_db:
#             wiki_hashes = car.wiki_hashes
#             wiki_cars = Wikipedia().get_cars_by_hashes(wiki_hashes)
#             fuel_type = car.fuel_type
#             brand_name = car.manufacturer
#             wiki_car: WikiCarModel
#             for wiki_car in wiki_cars:
#                 category = wiki_car.category_short_eu
#                 wiki_brand_name = wiki_car.brand_name
#                 wiki_car_name = wiki_brand_name + wiki_car.car_name
#                 processed_cars[category] = list()
#                 if car.hash_id not in processed_cars[category]:
#                     if category not in cars_per_category:
#                         cars_per_category[category] = dict()
#                         processed_brands[category] = list()
#                         cars_per_category[category]['car_counter'] = 0
#                         cars_per_category[category]['brand_counter'] = 0
#                         cars_per_category[category]['individual_cars'] = 0
#                         cars_per_category[category]['{}_counter'.format(fuel_type)] = 0
#                     if '{}_counter'.format(fuel_type) not in cars_per_category[category]:
#                         cars_per_category[category]['{}_counter'.format(fuel_type)] = 0
#                     if brand_name not in processed_brands[category]:
#                         cars_per_category[category]['brand_counter'] += 1
#                         processed_brands[category].append(brand_name)
#                     if wiki_car_name not in processed_cars[category]:
#                         cars_per_category[category]['individual_cars'] += 1
#                         processed_cars[category].append(wiki_car_name)
#                     cars_per_category[category]['car_counter'] += 1
#                     cars_per_category[category]['{}_counter'.format(fuel_type)] += 1
#                     processed_cars[category].append(car.hash_id)
#         return cars_per_category
#
#     def numb_cars_per_brand(self):
#         cars_per_category = dict()
#         cars_per_brand = dict()
#
#         car: CarfuelDataCarModel
#         for car in self.cfd_all_cars_db:
#             car_brand = car.manufacturer
#             fuel_type = car.fuel_type
#             wiki_hashes = car.wiki_hashes
#             wiki_cars = Wikipedia().get_cars_by_hashes(wiki_hashes)
#             wiki_car: WikiCarModel
#             for wiki_car in wiki_cars:
#                 category = wiki_car.category_short_eu
#                 if car_brand not in cars_per_brand:
#                     cars_per_brand[car_brand] = dict()
#                     cars_per_brand[car_brand]['categories'] = list()
#                     cars_per_brand[car_brand]['car_counter'] = 0
#                 if '{}_counter'.format(fuel_type) not in cars_per_brand[car_brand]:
#                     cars_per_brand[car_brand]['{}_counter'.format(fuel_type)] = 0
#                 if category not in cars_per_brand[car_brand]['categories']:
#                     cars_per_brand[car_brand]['categories'].append(category)
#                 cars_per_brand[car_brand]['car_counter'] += 1
#                 cars_per_brand[car_brand]['{}_counter'.format(fuel_type)] += 1
#         return cars_per_brand
#
#
# class ESDataDB:
#     def price_availability_countries(self):
#         logger.info("ES: Constructing price availability for countries stats")
#         country_price_availability = query_countries_w_prices()
#         return country_price_availability
#
#     def price_comp_de_eu(self):
#         pass
#
#
# class CFDConsumption:
#     geojson = None
#     simple_cfd_filter = None
#     categories = None
#
#     def __init__(self):
#         route_file = file_folder.joinpath('100km_geojson.json')
#         self.categories = Wikipedia().get_categories(ordered=True)
#         self.simple_cfd_filter = json.loads(
#             '{"data_source": "cfd","fuel_type": "gasoline","vehicle_type": "car", "vehicle_categories": ["all"]}')
#         with open(route_file, 'rb') as f:
#             self.geojson = json.load(f)
#
#     def calculate_stepping(self, stepping, end_kmh, category):
#         initial_stepping = 0
#         steppings_data = dict()  # Store each stepping
#         consumption_per_class = dict()
#         print("===> Consumption for category: {}".format(category))
#         consumption_per_class['total_consumption'] = dict()
#         while initial_stepping < end_kmh:
#             stepping_data = dict()  # consumption, co2, co, nox, thc, cost
#             initial_stepping += stepping
#             custom_cfd_filter = self.simple_cfd_filter
#             custom_cfd_filter['driving_speed'] = initial_stepping
#             request_json = {
#                 'request': 'route',
#                 'geometry': {
#                     'geojson': self.geojson,
#                     'filters': self.simple_cfd_filter
#                 }
#             }
#             response: request = client.post('/fuel?request=route', json=request_json)
#             json_response = json.loads(response.data)
#             category_fuel_stats = json_response['fuel_stats'][category]
#             if 'total_consumption' in category_fuel_stats:
#                 if initial_stepping == stepping:
#                     # Get general data once in the beginning
#                     cfd_cars = json_response['fuel_stats'][category]['category_info']['cfd_cars'] if 'cfd_cars' in \
#                                                                                                      json_response[
#                                                                                                          'fuel_stats'][
#                                                                                                          category][
#                                                                                                          'category_info'] else None
#                     ec_sensors = json_response['fuel_stats'][category]['category_info']['ec_sensors']
#                     ec_measurements = json_response['fuel_stats'][category]['category_info']['ec_measurements']
#                     if cfd_cars is not None:
#                         consumption_per_class['cfd_cars'] = cfd_cars
#                     consumption_per_class['ec_sensors'] = ec_sensors
#                     consumption_per_class['ec_measurements'] = ec_measurements
#                     print("({}/{}/{})".format(ec_sensors, cfd_cars if cfd_cars is not None else 0, ec_measurements))
#                 consumption = json_response['fuel_stats'][category]['total_consumption']['liters']
#                 consumption_per_class['total_consumption'][stepping] = consumption
#                 stepping_data['consumption'] = consumption
#                 print(initial_stepping, ", ", consumption)
#             else:
#                 stepping_data['consumption'] = "n"
#                 print(initial_stepping, ", ", 0)
#             if 'total_cost' in category_fuel_stats:
#                 stepping_data['cost'] = category_fuel_stats['total_cost']['w_tax_euro']
#             else:
#                 stepping_data['cost_ht'] = "n"
#                 stepping_data['cost_ttc'] = "n"
#             if 'total_emissions' in category_fuel_stats:
#                 steppings_data[initial_stepping] = stepping_data
#             if 'total_emissions' in category_fuel_stats and 'cfd_cars' in consumption_per_class:
#                 stepping_data['co2'] = category_fuel_stats['total_emissions']['co2_kg']
#
#                 stepping_data['co'] = category_fuel_stats['total_emissions']['co_g']
#                 stepping_data['nox'] = category_fuel_stats['total_emissions']['nox_g']
#                 stepping_data['thc'] = category_fuel_stats['total_emissions']['thc_g']
#             else:
#                 stepping_data['co2'] = "n"
#                 stepping_data['co'] = "n"
#                 stepping_data['nox'] = "n"
#                 stepping_data['thc'] = "n"
#         return steppings_data
#
#     def calculate_stepping_per_class(self, stepping, end_kmh):
#         route_data = dict()
#         for category in self.categories:
#             data = self.calculate_stepping(stepping, end_kmh, category)
#             route_data[category] = data
#         return route_data
