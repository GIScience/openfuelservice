from datetime import date

from numpy.core.multiarray import ndarray
from shapely.geometry import LineString

from openfuelservice.server import category_list, ofs_settings
from openfuelservice.server.base_calculations.envirocar import EnvirocarFuelModel, parse_ec_category_models
from openfuelservice.server.base_calculations.objects import Route, CountryLinePrice, GeneralLinePrice, \
    LinePriceCalculationObject
from openfuelservice.server.base_calculations.queries import query_cfd_average_category_statistics, query_cfd_category, \
    query_category_for_category_short, query_cfd_model
from openfuelservice.server.db_import.models import CarFuelDataAverageCategoryStatisticsModel, CarCategoryModel, \
    CarfuelDataCarModel
from openfuelservice.server.objects import Filters
from openfuelservice.server.utils.database.queries import CarFuelData
from openfuelservice.server.utils.misc.geometries import true_linestring_length

standard_epsg = ofs_settings['general']['advanced_settings']['standard_epsg']
vehicle_categories = category_list['car_categories']


def parse_cfd_id_model(filters):
    fuel_type: str = filters.fuel_type
    cfd_ids = filters.cfd_ids
    ec_fuel_models: dict = {}
    cfd_db_models = []
    cfd_car_fuel_models = []
    ec_categories = []
    cfd_id_categories = CarFuelData().get_cfd_categories(cfd_ids=cfd_ids)
    for cfd_id in cfd_ids:
        cfd_model = query_cfd_model(cfd_id=cfd_id)
        cfd_db_models.append(cfd_model)
    for cfd_id in cfd_id_categories:
        categories = cfd_id_categories[cfd_id]
        ec_categories.extend(category for category in categories if category not in ec_categories)
    ordered_ec_fuel_models = parse_ec_category_models(categories=ec_categories, ordered_categories=True,
                                                      filters=filters)
    cfd_model: CarfuelDataCarModel
    for cfd_model in cfd_db_models:
        cfd_categories: str = cfd_id_categories[cfd_model.hash_id]
        cfd_ec_fuel_models = []
        for category in ordered_ec_fuel_models:
            if category in cfd_categories and len(ordered_ec_fuel_models[category]) > 0:
                cfd_ec_fuel_models.extend(fuel_model for fuel_model in ordered_ec_fuel_models[category])
        fuel_model: CarFuelModel = CarFuelModel(ec_fuel_models=cfd_ec_fuel_models, cfd_db_model=cfd_model)
        cfd_car_fuel_models.append(fuel_model)
    return cfd_car_fuel_models


def parse_cfd_category_models(filters, categories: list) -> []:
    fuel_type: str = filters.fuel_type
    ec_fuel_models: dict = {}
    cfd_fuel_models: list = []
    cfd_ordered_av_cat_statistics = dict()
    year = filters.year
    ordered_ec_fuel_models = parse_ec_category_models(categories=categories, ordered_categories=True, filters=filters)
    if 'all' in categories:
        cfd_query: list = query_cfd_average_category_statistics(fuel_type=fuel_type)
    else:
        cfd_query = []
        for category in categories:
            category_query = query_cfd_category(fuel_type=fuel_type, category=category)
            cfd_query.extend(category_query)

    average_category_statistic: CarFuelDataAverageCategoryStatisticsModel
    for average_category_statistic in cfd_query:
        category: str = average_category_statistic.category_short_eu
        if category not in cfd_ordered_av_cat_statistics:
            cfd_ordered_av_cat_statistics[category] = []
        cfd_ordered_av_cat_statistics[category].append(average_category_statistic)

    category: str
    for category in cfd_ordered_av_cat_statistics:
        if category in ordered_ec_fuel_models and len(ordered_ec_fuel_models[category]) > 0:
            category_statistics: [CarFuelDataAverageCategoryStatisticsModel] = cfd_ordered_av_cat_statistics[category]
            fuel_model: CFDAverageFuelModel = CFDAverageFuelModel(ec_fuel_model=ordered_ec_fuel_models[category][0],
                                                                  category_statistics=category_statistics,
                                                                  category_short_eu=category, year=year)
            cfd_fuel_models.append(fuel_model)
    return cfd_fuel_models


class CFDFuelCalculationObject(object):
    def __init__(self):
        self.skip: bool = False
        self.result_fuel_liter_total: int = 0
        self.co2_gram_per_liter: int = 0
        self.co2_gram_per_km: int = 0
        self.co_mg_per_liter: int = 0
        self.co_mg_per_km: int = 0
        self.nox_mg_per_liter: int = 0
        self.nox_mg_per_km: int = 0
        self.thc_mg_per_liter: int = 0
        self.thc_mg_per_km: int = 0
        self.liter_per_100_km: int = 0
        self.length_km: int = 0
        self.fuel_consumption_growth_factor: int = 0
        self.fuel_consumption_cars: int = 0
        self.result_emissions_co2_g: int = 0
        self.result_emissions_co2_g_cars: int = 0
        self.result_emissions_co_mg: int = 0
        self.result_emissions_co_mg_cars: int = 0
        self.result_emissions_nox_mg: int = 0
        self.result_emissions_nox_mg_cars: int = 0
        self.result_emissions_thc_mg: int = 0
        self.result_emissions_thc_mg_cars: int = 0
        self.ec_categories = {}


class DistanceCalculationObject(object):
    def __init__(self):
        pass


class CarFuelModel(object):
    def __init__(self, ec_fuel_models: [EnvirocarFuelModel], cfd_db_model: CarfuelDataCarModel):
        self.ec_fuel_models: [EnvirocarFuelModel] = ec_fuel_models
        self.cfd_car_model: CarfuelDataCarModel = cfd_db_model
        self.fuel_type = self.cfd_car_model.fuel_type
        # The average speed represents the speed at which the cfd data was averagely taken
        self.average_speed = 63

        self.average_fuel_consumption_100_km: float = self.cfd_car_model.metric_combined

        self.emissions_co2_g_per_km: float = self.cfd_car_model.co2_g_per_km

        self.emissions_co_mg_per_km: float = self.cfd_car_model.emissions_co_mg_per_km

        self.emissions_nox_mg_per_km: float = self.cfd_car_model.emissions_nox_mg_per_km

        self.emissions_thc_mg_per_km: float = self.cfd_car_model.thc_emissions_mg_per_km

    def calculate_route(self, kmh: int, length_m: float,
                        manual_consumption_per_100km: float = None) -> CFDFuelCalculationObject:
        average_fuel_consumption_100_km = None
        calculation_object = CFDFuelCalculationObject()
        length_km: float = length_m * 0.0010000
        ec_fuel_model: EnvirocarFuelModel
        fuel_consumption_growth_factors, co2_consumption_growth_factors = [], []
        for ec_fuel_model in self.ec_fuel_models:
            fuel, co2 = ec_fuel_model.get_consumption_growth_factor(
                start_speed=self.average_speed, dest_speed=kmh)
            fuel_consumption_growth_factors.append(fuel)
            co2_consumption_growth_factors.append(co2)
            category = ec_fuel_model.category_short_eu
            sensors = ec_fuel_model.number_sensors
            if category not in calculation_object.ec_categories:
                calculation_object.ec_categories[category] = sensors
        fuel_factor = sum(fuel_consumption_growth_factors) / len(fuel_consumption_growth_factors)
        co2_factor = sum(co2_consumption_growth_factors) / len(co2_consumption_growth_factors)
        if self.average_fuel_consumption_100_km and \
                self.emissions_co2_g_per_km and \
                self.emissions_co_mg_per_km and \
                self.emissions_nox_mg_per_km and \
                self.emissions_thc_mg_per_km:
            if manual_consumption_per_100km is not None:
                average_fuel_consumption_per_100_km = manual_consumption_per_100km
            else:
                average_fuel_consumption_per_100_km = self.average_fuel_consumption_100_km
            average_fuel_consumption_per_km = average_fuel_consumption_per_100_km / 100
            raised_fuel_consumption_per_km = (average_fuel_consumption_per_km * fuel_factor) + average_fuel_consumption_per_km
            fuel_consumption_in_liters = length_km * raised_fuel_consumption_per_km
            average_emissions_co2_g_per_km = self.emissions_co2_g_per_km
            raised_co2_g_per_km = (average_emissions_co2_g_per_km * co2_factor) + average_emissions_co2_g_per_km
            raised_co2_g_per_liter: [] = raised_co2_g_per_km / raised_fuel_consumption_per_km

            calculation_object.result_fuel_liter_total = fuel_consumption_in_liters
            calculation_object.co2_gram_per_liter = raised_co2_g_per_liter
            calculation_object.co2_gram_per_km = raised_co2_g_per_km
            calculation_object.result_emissions_co2_g = raised_co2_g_per_km * length_km
            calculation_object.result_emissions_co2_g_cars = 1

            co_mg_per_km = self.emissions_co_mg_per_km
            raised_co_mg_per_km = (co_mg_per_km * fuel_factor) + co_mg_per_km
            calculation_object.co_mg_per_km = raised_co_mg_per_km
            calculation_object.co_mg_per_liter = raised_co_mg_per_km / raised_fuel_consumption_per_km
            calculation_object.result_emissions_co_mg = raised_co_mg_per_km * length_km
            calculation_object.result_emissions_co_mg_cars = 1

            nox_mg_per_km = self.emissions_nox_mg_per_km
            raised_nox_mg_per_km = (nox_mg_per_km * fuel_factor) + nox_mg_per_km
            calculation_object.nox_mg_per_km = raised_nox_mg_per_km
            calculation_object.nox_mg_per_liter = raised_nox_mg_per_km / raised_fuel_consumption_per_km
            calculation_object.result_emissions_nox_mg = raised_nox_mg_per_km * length_km
            calculation_object.result_emissions_nox_mg_cars = 1

            thc_mg_per_km = self.emissions_thc_mg_per_km
            raised_thc_mg_per_km = (thc_mg_per_km * fuel_factor) + thc_mg_per_km
            calculation_object.thc_mg_per_km = raised_thc_mg_per_km
            calculation_object.thc_mg_per_liter = raised_thc_mg_per_km / raised_fuel_consumption_per_km
            calculation_object.result_emissions_thc_mg = raised_thc_mg_per_km * length_km
            calculation_object.result_emissions_thc_mg_cars = 1

            if manual_consumption_per_100km is not None:
                calculation_object.fuel_consumption_cars = 1
            else:
                calculation_object.fuel_consumption_cars = 1

            calculation_object.liter_per_100_km = raised_fuel_consumption_per_km * 100
            return calculation_object
        else:
            calculation_object.skip = True
            return calculation_object


class AverageFuelModel(object):
    def __init__(self, ec_fuel_model: EnvirocarFuelModel, category_statistics: []):
        self.ec_fuel_model: EnvirocarFuelModel = ec_fuel_model
        self.cfd_category_statistics = category_statistics

    def get_phenomenon_values(self, phenomenon_name: str, year: int = None) -> dict:
        statistic: CarFuelDataAverageCategoryStatisticsModel
        return_dict = dict()
        average_phenomenon_values = []
        phenomenon_weights = []
        for statistic in self.cfd_category_statistics:
            if statistic.phenomenon_name == phenomenon_name:
                if year is not None and int(statistic.year) >= int(year):
                    average_phenomenon_values.append(statistic.value)
                    phenomenon_weights.append(statistic.numb_cars)
                elif year is None:
                    average_phenomenon_values.append(statistic.value)
                    phenomenon_weights.append(statistic.numb_cars)
        return_dict['values'] = average_phenomenon_values
        return_dict['weights'] = phenomenon_weights
        return return_dict

    def calculate_route(self, kmh: int, length_m: float,
                        manual_consumption_per_100km: float = None) -> CFDFuelCalculationObject:
        pass


class CFDAverageFuelModel(AverageFuelModel):

    def __init__(self, ec_fuel_model: EnvirocarFuelModel, category_statistics: [],
                 category_short_eu: str, year: int = None):
        super().__init__(ec_fuel_model=ec_fuel_model, category_statistics=category_statistics)
        self.category_short_eu = category_short_eu
        self.fuel_type = self.ec_fuel_model.fuel_type
        # The average speed represents the speed at which the cfd data was averagely taken
        self.average_speed = 63

        self.average_fuel_consumption_100_km: dict = self.get_phenomenon_values(phenomenon_name='metric_combined',
                                                                                year=year)

        self.emissions_co2_g_per_km: dict = self.get_phenomenon_values(phenomenon_name='co2_g_per_km', year=year)

        self.emissions_co_mg_per_km: dict = self.get_phenomenon_values(phenomenon_name='emissions_co_mg_per_km',
                                                                       year=year)

        self.emissions_nox_mg_per_km: dict = self.get_phenomenon_values(phenomenon_name='emissions_nox_mg_per_km',
                                                                        year=year)

        self.emissions_thc_mg_per_km: dict = self.get_phenomenon_values(phenomenon_name='thc_emissions_mg_per_km',
                                                                        year=year)

    def calculate_route(self, kmh: int, length_m: float,
                        manual_consumption_per_100km: float = None) -> CFDFuelCalculationObject():
        average_fuel_consumption_100_km = None
        calculation_object = CFDFuelCalculationObject()
        length_km: float = length_m * 0.0010000
        fuel_consumption_growth_factor, co2_consumption_growth_factor = self.ec_fuel_model.get_consumption_growth_factor(
            start_speed=self.average_speed,
            dest_speed=kmh)
        if len(self.average_fuel_consumption_100_km['values']) > 0 and len(
                self.emissions_co2_g_per_km['values']) > 0 and \
                len(self.emissions_co_mg_per_km['values']) > 0 and len(self.emissions_nox_mg_per_km['values']) > 0 and \
                len(self.emissions_thc_mg_per_km['values']) > 0:
            if manual_consumption_per_100km is not None:
                average_fuel_consumption_per_100_km = manual_consumption_per_100km
            else:
                average_fuel_consumption_per_100_km = (sum(self.average_fuel_consumption_100_km['values']) / len(
                    self.average_fuel_consumption_100_km['values']))
            average_fuel_consumption_per_km = average_fuel_consumption_per_100_km / 100
            raised_fuel_consumption_per_km = (
                                                     average_fuel_consumption_per_km * fuel_consumption_growth_factor) + average_fuel_consumption_per_km
            fuel_consumption_in_liters = length_km * raised_fuel_consumption_per_km
            average_emissions_co2_g_per_km = sum(self.emissions_co2_g_per_km['values']) / len(
                self.emissions_co_mg_per_km['values'])
            raised_co2_g_per_km = (
                                          average_emissions_co2_g_per_km * co2_consumption_growth_factor) + average_emissions_co2_g_per_km
            raised_co2_g_per_liter: [] = raised_co2_g_per_km / raised_fuel_consumption_per_km

            calculation_object.result_fuel_liter_total = fuel_consumption_in_liters
            calculation_object.co2_gram_per_liter = raised_co2_g_per_liter
            calculation_object.co2_gram_per_km = raised_co2_g_per_km
            calculation_object.result_emissions_co2_g = raised_co2_g_per_km * length_km
            calculation_object.result_emissions_co2_g_cars = sum(self.emissions_co2_g_per_km['weights'])

            co_mg_per_km = sum(self.emissions_co_mg_per_km['values']) / len(self.emissions_co_mg_per_km['values'])
            raised_co_mg_per_km = (co_mg_per_km * fuel_consumption_growth_factor) + co_mg_per_km
            calculation_object.co_mg_per_km = raised_co_mg_per_km
            calculation_object.co_mg_per_liter = raised_co_mg_per_km / raised_fuel_consumption_per_km
            calculation_object.result_emissions_co_mg = raised_co_mg_per_km * length_km
            calculation_object.result_emissions_co_mg_cars = sum(self.emissions_co_mg_per_km['weights'])

            nox_mg_per_km = sum(self.emissions_nox_mg_per_km['values']) / len(self.emissions_nox_mg_per_km['values'])
            raised_nox_mg_per_km = (nox_mg_per_km * fuel_consumption_growth_factor) + nox_mg_per_km
            calculation_object.nox_mg_per_km = raised_nox_mg_per_km
            calculation_object.nox_mg_per_liter = raised_nox_mg_per_km / raised_fuel_consumption_per_km
            calculation_object.result_emissions_nox_mg = raised_nox_mg_per_km * length_km
            calculation_object.result_emissions_nox_mg_cars = sum(self.emissions_nox_mg_per_km['weights'])

            thc_mg_per_km = sum(self.emissions_thc_mg_per_km['values']) / len(self.emissions_thc_mg_per_km['values'])
            raised_thc_mg_per_km = (thc_mg_per_km * fuel_consumption_growth_factor) + thc_mg_per_km
            calculation_object.thc_mg_per_km = raised_thc_mg_per_km
            calculation_object.thc_mg_per_liter = raised_thc_mg_per_km / raised_fuel_consumption_per_km
            calculation_object.result_emissions_thc_mg = raised_thc_mg_per_km * length_km
            calculation_object.result_emissions_thc_mg_cars = sum(self.emissions_thc_mg_per_km['weights'])

            if manual_consumption_per_100km is not None:
                calculation_object.fuel_consumption_cars = 1
            else:
                calculation_object.fuel_consumption_cars = sum(self.average_fuel_consumption_100_km['weights'])

            calculation_object.liter_per_100_km = raised_fuel_consumption_per_km * 100
            return calculation_object
        else:
            calculation_object.skip = True
            return calculation_object


class DistanceCalculation(Route):
    # Entry Point
    def __init__(self, geom: LineString, filters: Filters):
        super().__init__(geom=geom, filters=filters)
        if filters.driving_speed is None:
            driving_style: str = self.filters.driving_style
            self.average_speed: int = ofs_settings['general']['advanced_settings']['average_speeds'][driving_style]
        else:
            self.average_speed = filters.driving_speed
        if filters.cfd_ids is not None:
            self.fuel_models: [CarFuelModel] = parse_cfd_id_model(filters=self.filters)
        else:
            self.fuel_models: [CFDAverageFuelModel] = parse_cfd_category_models(filters=self.filters,
                                                                                categories=self.categories)
        self.result_categories = dict()

    def calculate_individual_cfd_cost(self) -> dict:
        tank_sizes: dict = self.filters.tank_sizes
        fuel_consumptions = self.filters.fuel_consumptions
        fuel_type = self.filters.fuel_type
        route_result = dict()
        fuel_model: CarFuelModel
        category_short = 'individual'
        cfd_car_counter = 0
        ec_categories = {}
        for fuel_model in self.fuel_models:
            skip_category: bool = False
            if type(fuel_model) != CarFuelModel:
                continue
            else:
                cfd_car_counter += 1
            if fuel_model.fuel_type != fuel_type:
                continue
            tank_size: int = None
            manual_consumption_per_100_km: float = None
            if fuel_consumptions is not None and category_short in fuel_consumptions:
                manual_consumption_per_100_km = float(fuel_consumptions[category_short])
            if tank_sizes is None or category_short not in tank_sizes:
                tank_size = int(vehicle_categories[category_short]['tank_capacity'])
            else:
                tank_size = int(tank_sizes[category_short])

            if category_short == 'individual':
                category_object: CarCategoryModel = CarCategoryModel()
                category_object.category_name_de = 'Individuell'
                category_object.category_name_en = 'individual'
            else:
                category_object: CarCategoryModel = query_category_for_category_short(category_short_eu=category_short)
            if category_short not in route_result:
                route_result[category_short] = dict()
                route_result[category_short]['total_emissions'] = dict()
                route_result[category_short]['fuel_factors'] = dict()
                route_result[category_short]['total_consumption'] = dict()
                route_result[category_short]['total_cost'] = dict()
                route_result[category_short]['route'] = dict()

                route_result[category_short]['category_info'] = dict()
                route_result[category_short]['category_info']['en'] = category_object.category_name_en
                route_result[category_short]['category_info']['de'] = category_object.category_name_de
                route_result[category_short]['category_info'][
                    'manual_consumption'] = True if manual_consumption_per_100_km is not None else False
                route_result[category_short]['category_info']['cfd_cars'] = len(self.fuel_models)
                route_result[category_short]['category_info']['ec_sensors'] = 0
                route_result[category_short]['category_info']['ec_sensors'] = 0
                route_result[category_short]['total_emissions']['co2_kg'] = 0
                route_result[category_short]['total_emissions']['co_g'] = 0
                route_result[category_short]['total_emissions']['nox_g'] = 0
                route_result[category_short]['total_emissions']['thc_g'] = 0
                route_result[category_short]['total_consumption']['liters'] = 0
                route_result[category_short]['total_cost']['w_tax_euro'] = 0
                route_result[category_short]['total_cost']['wo_tax_euro'] = 0
                route_result[category_short]['fuel_factors']['liter_per_100km'] = 0
                route_result[category_short]['fuel_factors']['co2_gram_per_km'] = 0
                route_result[category_short]['fuel_factors']['co2_gram_per_liter'] = 0
                route_result[category_short]['fuel_factors']['co_mg_per_km'] = 0
                route_result[category_short]['fuel_factors']['co_mg_per_liter'] = 0
                route_result[category_short]['fuel_factors']['nox_mg_per_km'] = 0
                route_result[category_short]['fuel_factors']['nox_mg_per_liter'] = 0
                route_result[category_short]['fuel_factors']['thc_mg_per_km'] = 0
                route_result[category_short]['fuel_factors']['thc_mg_per_liter'] = 0


            result_liter_100: [float] or float = 0
            cost_date: date = None
            total_liters: [float] or float = 0

            # Emission variables
            total_co2_gram: [float] or float = 0
            total_co_mg: [float] or float = 0
            total_nox_mg: [float] or float = 0
            total_thc_mg: [float] or float = 0
            total_cfd_cars = 0

            # Cost Variables
            cost_tax: [float] or float = 0
            cost_wo_tax: [float] or float = 0
            total_km: [float] or float = 0

            previous_price_model: CountryLinePrice = None
            remaining_fuel: float = 0
            for price_model in self.price_models:
                price_model: CountryLinePrice or GeneralLinePrice
                if previous_price_model is None:
                    previous_price_model = price_model
                remaining_fuel_cost_tax: float = 0
                remaining_fuel_cost_wo_tax: float = 0
                if remaining_fuel > 0:
                    price_calculation: LinePriceCalculationObject = previous_price_model.calculate_cost(
                        liter=remaining_fuel,
                        fuel_type=fuel_type)
                    previous_price_model = price_model
                    cost_tax += price_calculation.fuel_cost_tax
                    cost_wo_tax += price_calculation.fuel_cost_wo_tax

                length_m = true_linestring_length(linestring=price_model.linestring)
                total_km += length_m / 1000
                fuel_calculation: CFDFuelCalculationObject = fuel_model.calculate_route(
                    kmh=self.average_speed, length_m=length_m)
                for ec_category in fuel_calculation.ec_categories:
                    if ec_category not in ec_categories:
                        ec_categories[ec_category] = fuel_calculation.ec_categories[ec_category]
                if fuel_calculation.skip:
                    skip_category = True
                    route_result[category_short] = dict()
                    route_result[category_short]['category_info'] = dict()
                    route_result[category_short]['category_info']['en'] = category_object.category_name_en
                    route_result[category_short]['category_info']['de'] = category_object.category_name_de
                    route_result[category_short]['category_info'][
                        'manual_consumption'] = True if manual_consumption_per_100_km is not None else False

                    break
                result_fuel_liter_total = fuel_calculation.result_fuel_liter_total
                result_liter_100: [float] or float = fuel_calculation.liter_per_100_km
                total_co2_gram += fuel_calculation.result_emissions_co2_g
                total_co_mg += fuel_calculation.result_emissions_co_mg
                total_nox_mg += fuel_calculation.result_emissions_nox_mg
                total_thc_mg += fuel_calculation.result_emissions_thc_mg
                total_liters += result_fuel_liter_total

                if remaining_fuel > 0:
                    result_fuel_liter_total -= remaining_fuel
                    remaining_fuel = 0
                needed_refueling_theory = result_fuel_liter_total / tank_size
                needed_refueling_actual = round(needed_refueling_theory, 5)
                if tank_size * needed_refueling_actual - fuel_calculation.result_fuel_liter_total > 0:
                    remaining_fuel = tank_size * needed_refueling_actual - fuel_calculation.result_fuel_liter_total
                price_calculation: LinePriceCalculationObject = price_model.calculate_cost(
                    liter=result_fuel_liter_total,
                    fuel_type=fuel_type)
                cost_date = price_calculation.cost_date
                cost_tax += price_calculation.fuel_cost_tax
                cost_wo_tax += price_calculation.fuel_cost_wo_tax
            if skip_category:
                route_result[category_short]['category_info'][
                    'calculation_errors'] = 'Not enough data to calculate the Category'
            else:
                route_result[category_short]['category_info']['calculation_errors'] = 'No Errors'
                route_result[category_short]['category_info']['ec_sensors'] += len(fuel_model.ec_fuel_models)
                route_result[category_short]['total_emissions']['co2_kg'] += (total_co2_gram / 1000)
                route_result[category_short]['total_emissions']['co_g'] += (total_co_mg / 1000)
                route_result[category_short]['total_emissions']['nox_g'] += (total_nox_mg / 1000)
                route_result[category_short]['total_emissions']['thc_g'] += (total_thc_mg / 1000)
                route_result[category_short]['total_consumption']['liters'] += total_liters
                route_result[category_short]['total_cost']['w_tax_euro'] += cost_tax
                route_result[category_short]['total_cost']['wo_tax_euro'] += cost_wo_tax
                route_result[category_short]['total_cost']['price_date'] = cost_date.strftime('%Y-%m-%dT%H:%M:%S')
                route_result[category_short]['fuel_factors']['liter_per_100km'] += result_liter_100
                route_result[category_short]['fuel_factors']['co2_gram_per_km'] += fuel_calculation.co2_gram_per_km
                route_result[category_short]['fuel_factors']['co2_gram_per_liter'] += fuel_calculation.co2_gram_per_liter
                route_result[category_short]['fuel_factors']['co_mg_per_km'] += fuel_calculation.co_mg_per_km
                route_result[category_short]['fuel_factors']['co_mg_per_liter'] += fuel_calculation.co_mg_per_liter
                route_result[category_short]['fuel_factors']['nox_mg_per_km'] += fuel_calculation.nox_mg_per_km
                route_result[category_short]['fuel_factors']['nox_mg_per_liter'] += fuel_calculation.nox_mg_per_liter
                route_result[category_short]['fuel_factors']['thc_mg_per_km'] += fuel_calculation.thc_mg_per_km
                route_result[category_short]['fuel_factors']['thc_mg_per_liter'] += fuel_calculation.thc_mg_per_liter

        total_ec_sensors = 0
        for ec_category in ec_categories:
            ec_cars = ec_categories[ec_category]
            total_ec_sensors += ec_cars
        route_result[category_short]['category_info']['ec_sensors'] =  total_ec_sensors
        route_result[category_short]['total_emissions']['co2_kg'] = round(route_result[category_short]['total_emissions']['co2_kg'] / cfd_car_counter, 6)
        route_result[category_short]['total_emissions']['co_g'] = round(route_result[category_short]['total_emissions']['co_g'] / cfd_car_counter, 6)
        route_result[category_short]['total_emissions']['nox_g'] = round(route_result[category_short]['total_emissions']['nox_g'] / cfd_car_counter, 6)
        route_result[category_short]['total_emissions']['thc_g'] = round(route_result[category_short]['total_emissions']['thc_g'] / cfd_car_counter, 6)
        route_result[category_short]['total_consumption']['liters'] = round(route_result[category_short]['total_consumption']['liters'] / cfd_car_counter, 2)
        route_result[category_short]['total_cost']['w_tax_euro'] = round(route_result[category_short]['total_cost']['w_tax_euro'] / cfd_car_counter, 2)
        route_result[category_short]['total_cost']['wo_tax_euro'] = round(route_result[category_short]['total_cost']['wo_tax_euro'] / cfd_car_counter, 2)
        route_result[category_short]['fuel_factors']['liter_per_100km'] = round(route_result[category_short]['fuel_factors']['liter_per_100km'] / cfd_car_counter, 1)
        route_result[category_short]['fuel_factors']['co2_gram_per_km'] = round(route_result[category_short]['fuel_factors']['co2_gram_per_km'] / cfd_car_counter, 6)
        route_result[category_short]['fuel_factors']['co2_gram_per_liter'] = round(route_result[category_short]['fuel_factors']['co2_gram_per_liter'] / cfd_car_counter, 6)
        route_result[category_short]['fuel_factors']['co_mg_per_km'] = round(route_result[category_short]['fuel_factors']['co_mg_per_km'] / cfd_car_counter, 6)
        route_result[category_short]['fuel_factors']['co_mg_per_liter'] = round(route_result[category_short]['fuel_factors']['co_mg_per_liter'] / cfd_car_counter, 6)
        route_result[category_short]['fuel_factors']['nox_mg_per_km'] = round(route_result[category_short]['fuel_factors']['nox_mg_per_km'] / cfd_car_counter, 6)
        route_result[category_short]['fuel_factors']['nox_mg_per_liter'] = round(route_result[category_short]['fuel_factors']['nox_mg_per_liter'] / cfd_car_counter, 6)
        route_result[category_short]['fuel_factors']['thc_mg_per_km'] = round(route_result[category_short]['fuel_factors']['thc_mg_per_km'] / cfd_car_counter, 6)
        route_result[category_short]['fuel_factors']['thc_mg_per_liter'] = round(route_result[category_short]['fuel_factors']['thc_mg_per_liter'] / cfd_car_counter, 6)

        route_result[category_short]['route']['km'] = round(self.route_length/1000, 2)
        return route_result

    def calculate_category_cost(self) -> dict:
        # TODO Add the differentiation here if it is CarFuelModel or AverageFuelModel and split to two functions than
        tank_sizes: dict = self.filters.tank_sizes
        fuel_consumptions = self.filters.fuel_consumptions
        route_result = dict()
        fuel_model: CFDAverageFuelModel
        # TODO get the route parts before!
        for fuel_model in self.fuel_models:
            skip_category: bool = False
            category_short_eu = fuel_model.category_short_eu
            tank_size: int = None
            manual_consumption_per_100_km: float = None
            fuel_type = fuel_model.fuel_type
            if fuel_consumptions is not None and category_short_eu in fuel_consumptions:
                manual_consumption_per_100_km = float(fuel_consumptions[category_short_eu])
            if tank_sizes == None or category_short_eu not in tank_sizes:
                tank_size = int(vehicle_categories[category_short_eu]['tank_capacity'])
            else:
                tank_size = int(tank_sizes[category_short_eu])

            category_object: CarCategoryModel = query_category_for_category_short(
                category_short_eu=category_short_eu)
            if category_short_eu not in route_result:
                route_result[category_short_eu] = dict()
                route_result[category_short_eu]['total_emissions'] = dict()
                route_result[category_short_eu]['fuel_factors'] = dict()
                route_result[category_short_eu]['total_consumption'] = dict()
                route_result[category_short_eu]['total_cost'] = dict()
                route_result[category_short_eu]['route'] = dict()

                route_result[category_short_eu]['category_info'] = dict()
                route_result[category_short_eu]['category_info']['en'] = category_object.category_name_en
                route_result[category_short_eu]['category_info']['de'] = category_object.category_name_de
                route_result[category_short_eu]['category_info'][
                    'manual_consumption'] = True if manual_consumption_per_100_km is not None else False

            result_liter_100: [float] or float = 0
            cost_date: date = None
            total_liters: [float] or float = 0

            # Emission variables
            total_co2_gram: [float] or float = 0
            total_co_mg: [float] or float = 0
            total_nox_mg: [float] or float = 0
            total_thc_mg: [float] or float = 0
            total_cfd_cars = 0
            co2_gram_per_km = 0
            co_mg_per_km = 0
            nox_mg_per_km = 0
            thc_mg_per_km = 0
            co2_gram_per_liter = 0
            co_mg_per_liter = 0
            nox_mg_per_liter = 0
            thc_mg_per_liter = 0
            fuel_consumption_cars = 0

            # Cost Variables
            cost_tax: [float] or float = 0
            cost_wo_tax: [float] or float = 0
            total_km: [float] or float = 0

            previous_price_model: CountryLinePrice = None
            remaining_fuel: float = 0
            for price_model in self.price_models:
                price_model: CountryLinePrice or GeneralLinePrice
                if previous_price_model == None:
                    previous_price_model = price_model
                remaining_fuel_cost_tax: float = 0
                remaining_fuel_cost_wo_tax: float = 0
                if remaining_fuel > 0:
                    price_calculation: LinePriceCalculationObject = previous_price_model.calculate_cost(
                        liter=remaining_fuel,
                        fuel_type=fuel_type)
                    previous_price_model = price_model
                    cost_tax += price_calculation.fuel_cost_tax
                    cost_wo_tax += price_calculation.fuel_cost_wo_tax

                length_m = true_linestring_length(linestring=price_model.linestring)
                total_km += length_m / 1000
                fuel_calculation: CFDFuelCalculationObject = fuel_model.calculate_route(
                    kmh=self.average_speed, length_m=length_m)
                if fuel_calculation.skip is True:
                    skip_category = True
                    route_result[category_short_eu] = dict()
                    route_result[category_short_eu]['category_info'] = dict()
                    route_result[category_short_eu]['category_info']['en'] = category_object.category_name_en
                    route_result[category_short_eu]['category_info']['de'] = category_object.category_name_de
                    route_result[category_short_eu]['category_info'][
                        'manual_consumption'] = True if manual_consumption_per_100_km is not None else False

                    break
                result_fuel_liter_total = fuel_calculation.result_fuel_liter_total
                result_liter_100: [float] or float = fuel_calculation.liter_per_100_km
                result_co2_gram_per_km: [float] or float = fuel_calculation.co2_gram_per_km
                co2_gram_per_liter: [float] or float = fuel_calculation.co2_gram_per_liter
                total_co2_gram += fuel_calculation.result_emissions_co2_g
                total_co_mg += fuel_calculation.result_emissions_co_mg
                total_nox_mg += fuel_calculation.result_emissions_nox_mg
                total_thc_mg += fuel_calculation.result_emissions_thc_mg

                total_co2_gram_cars = fuel_calculation.result_emissions_co2_g_cars
                total_co_mg_cars = fuel_calculation.result_emissions_co_mg_cars
                total_nox_mg_cars = fuel_calculation.result_emissions_nox_mg_cars
                total_thc_mg_cars = fuel_calculation.result_emissions_thc_mg_cars
                total_cfd_cars = (
                                         total_co2_gram_cars + total_co_mg_cars + total_nox_mg_cars + total_thc_mg_cars) / 4
                co2_gram_per_km = fuel_calculation.co2_gram_per_km
                co_mg_per_km = fuel_calculation.co_mg_per_km
                nox_mg_per_km = fuel_calculation.nox_mg_per_km
                thc_mg_per_km = fuel_calculation.thc_mg_per_km
                co2_gram_per_liter = fuel_calculation.co2_gram_per_liter
                co_mg_per_liter = fuel_calculation.co_mg_per_liter
                nox_mg_per_liter = fuel_calculation.nox_mg_per_liter
                thc_mg_per_liter = fuel_calculation.thc_mg_per_liter
                fuel_consumption_cars = fuel_calculation.fuel_consumption_cars

                total_liters += result_fuel_liter_total
                if remaining_fuel > 0:
                    result_fuel_liter_total -= remaining_fuel
                    remaining_fuel = 0
                needed_refueling_theory = result_fuel_liter_total / tank_size
                needed_refueling_actual = round(needed_refueling_theory, 5)
                if tank_size * needed_refueling_actual - fuel_calculation.result_fuel_liter_total > 0:
                    remaining_fuel = tank_size * needed_refueling_actual - fuel_calculation.result_fuel_liter_total
                price_calculation: LinePriceCalculationObject = price_model.calculate_cost(
                    liter=result_fuel_liter_total,
                    fuel_type=fuel_type)
                cost_date = price_calculation.cost_date
                cost_tax += price_calculation.fuel_cost_tax
                cost_wo_tax += price_calculation.fuel_cost_wo_tax
            if skip_category:
                route_result[category_short_eu]['category_info'][
                    'calculation_errors'] = 'Not enough data to calculate the Category'
            else:
                route_result[category_short_eu]['category_info']['calculation_errors'] = 'No Errors'
                route_result[category_short_eu]['category_info']['cfd_cars'] = int(
                    round(total_cfd_cars if type(total_cfd_cars) == ndarray else total_cfd_cars, 0))
                route_result[category_short_eu]['category_info'][
                    'ec_sensors'] = fuel_model.ec_fuel_model.number_sensors
                route_result[category_short_eu]['category_info'][
                    'ec_measurements'] = fuel_model.ec_fuel_model.number_measurements
                route_result[category_short_eu]['total_emissions']['co2_kg'] = round(
                    total_co2_gram[0] / 1000 if type(total_co2_gram) == ndarray else total_co2_gram / 1000, 6)
                route_result[category_short_eu]['total_emissions']['co_g'] = round(
                    total_co_mg[0] / 1000 if type(total_co_mg) == ndarray else total_co_mg / 1000, 6)
                route_result[category_short_eu]['total_emissions']['nox_g'] = round(
                    total_nox_mg[0] / 1000 if type(total_nox_mg) == ndarray else total_nox_mg / 1000, 6)
                route_result[category_short_eu]['total_emissions']['thc_g'] = round(
                    total_thc_mg[0] / 1000 if type(total_thc_mg) == ndarray else total_thc_mg / 1000, 6)

                route_result[category_short_eu]['total_consumption']['liters'] = round(total_liters[0] if type(
                    total_liters) == ndarray else total_liters, 2)

                route_result[category_short_eu]['total_cost']['w_tax_euro'] = round(
                    cost_tax[0] if type(cost_tax) == ndarray else cost_tax, 2)
                route_result[category_short_eu]['total_cost']['wo_tax_euro'] = round(
                    cost_wo_tax[0] if type(cost_wo_tax) == ndarray else cost_wo_tax, 2)
                route_result[category_short_eu]['total_cost']['price_date'] = cost_date.strftime(
                    '%Y-%m-%dT%H:%M:%S')

                route_result[category_short_eu]['fuel_factors']['liter_per_100km'] = round(
                    result_liter_100[0] if type(result_liter_100) == ndarray else result_liter_100, 1)
                route_result[category_short_eu]['fuel_factors']['co2_gram_per_km'] = round(
                    co2_gram_per_km[0] if type(co2_gram_per_km) == ndarray else co2_gram_per_km, 6)
                route_result[category_short_eu]['fuel_factors']['co2_gram_per_liter'] = round(
                    co2_gram_per_liter[0] if type(co2_gram_per_liter) == ndarray else co2_gram_per_liter, 6)
                route_result[category_short_eu]['fuel_factors']['co_mg_per_km'] = round(
                    co_mg_per_km[0] if type(co_mg_per_km) == ndarray else co_mg_per_km, 6)
                route_result[category_short_eu]['fuel_factors']['co_mg_per_liter'] = round(
                    co_mg_per_liter[0] if type(co_mg_per_liter) == ndarray else co_mg_per_liter, 6)
                route_result[category_short_eu]['fuel_factors']['nox_mg_per_km'] = round(
                    nox_mg_per_km[0] if type(nox_mg_per_km) == ndarray else nox_mg_per_km, 6)
                route_result[category_short_eu]['fuel_factors']['nox_mg_per_liter'] = round(
                    nox_mg_per_liter[0] if type(nox_mg_per_liter) == ndarray else nox_mg_per_liter, 6)
                route_result[category_short_eu]['fuel_factors']['thc_mg_per_km'] = round(
                    thc_mg_per_km[0] if type(thc_mg_per_km) == ndarray else thc_mg_per_km, 6)
                route_result[category_short_eu]['fuel_factors']['thc_mg_per_liter'] = round(
                    thc_mg_per_liter[0] if type(thc_mg_per_liter) == ndarray else thc_mg_per_liter, 6)

                route_result[category_short_eu]['route']['km'] = round(
                    total_km[0] if type(total_km) == ndarray else total_km, 6)
        for category in vehicle_categories:
            if category not in route_result:
                route_result[category] = dict()
                route_result[category]['category_info'] = dict()
                route_result[category]['category_info']['en'] = vehicle_categories[category]['en']
                route_result[category]['category_info']['de'] = vehicle_categories[category]['de']
                route_result[category]['category_info'][
                    'calculation_errors'] = 'Not enough data to calculate the Category'
        return route_result
