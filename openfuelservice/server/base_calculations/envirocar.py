import math
from datetime import date
from decimal import Decimal

from numpy import ndarray
from scipy import array
from scipy.interpolate import interp1d
from shapely.geometry import LineString

from openfuelservice.server import category_list, ofs_settings
from openfuelservice.server.base_calculations.objects import CountryLinePrice, GeneralLinePrice, Route, \
    LinePriceCalculationObject
from openfuelservice.server.base_calculations.queries import query_ec_average_category_statistics, query_ec_category, \
    query_category_for_category_short
from openfuelservice.server.db_import.models import EnvirocarAverageVehicleTypeStatisticModel, \
    EnvirocarAverageCategoryStatisticsModel, \
    CarCategoryModel
from openfuelservice.server.objects import Filters
from openfuelservice.server.utils.misc.geometries import true_linestring_length

standard_epsg = ofs_settings['general']['advanced_settings']['standard_epsg']
vehicle_categories = category_list['car_categories']


def parse_ec_category_models(filters, categories: list, ordered_categories: bool = False) -> list or dict:
    fuel_type: str = filters.fuel_type
    ordered_av_cat_statistics = {}
    if 'all' in categories:
        query: list = query_ec_average_category_statistics(fuel_type=fuel_type)
    else:
        query = []
        for category in categories:
            category_query = query_ec_category(fuel_type=fuel_type, category=category)
            query.extend(category_query)
    average_category_statistic: EnvirocarAverageCategoryStatisticsModel
    for average_category_statistic in query:
        category: str = average_category_statistic.category_short_eu
        if category not in ordered_av_cat_statistics:
            ordered_av_cat_statistics[category] = []
        ordered_av_cat_statistics[category].append(average_category_statistic)

    if ordered_categories:
        ordered_fuel_models = {}
        category: str
        for category in ordered_av_cat_statistics:
            if category not in ordered_fuel_models:
                ordered_fuel_models[category] = []
            if len(ordered_av_cat_statistics[category]) >= 3:
                category_object: [EnvirocarAverageCategoryStatisticsModel] = ordered_av_cat_statistics[category]
                fuel_model: EnvirocarFuelModel = EnvirocarFuelModel(category_statistics=category_object)
                ordered_fuel_models[category].append(fuel_model)
        return ordered_fuel_models
    else:
        fuel_models: list = []
        category: str
        for category in ordered_av_cat_statistics:
            if len(ordered_av_cat_statistics[category]) >= 3:
                category_object: [EnvirocarAverageCategoryStatisticsModel] = ordered_av_cat_statistics[category]
                fuel_model: EnvirocarFuelModel = EnvirocarFuelModel(category_statistics=category_object)
                fuel_models.append(fuel_model)
        return fuel_models


class AdvancedDistanceCalculation(Route):
    def __init__(self, geom: LineString, filters: Filters):
        super().__init__(geom=geom, filters=filters)
        self.fuel_models: [EnvirocarFuelModel] = parse_ec_category_models(filters=self.filters,
                                                                          categories=self.categories)
        if filters.driving_speed is None:
            driving_style: str = self.filters.driving_style
            self.average_speed: int = ofs_settings['general']['advanced_settings']['average_speeds'][driving_style]
        else:
            self.average_speed = filters.driving_speed
        self.result_categories = dict()

    def calculate_cost(self) -> dict:
        tank_sizes: dict = self.filters.tank_sizes
        fuel_consumptions = self.filters.fuel_consumptions
        route_result = dict()
        for fuel_model in self.fuel_models:
            tank_size: int = None
            manual_consumption_per_100_km: float = None
            fuel_model: EnvirocarFuelModel
            category_short_eu = fuel_model.category_short_eu
            if fuel_consumptions is not None and category_short_eu in fuel_consumptions:
                manual_consumption_per_100_km = float(fuel_consumptions[category_short_eu])
            if tank_sizes == None or category_short_eu not in tank_sizes:
                tank_size = int(vehicle_categories[category_short_eu]['tank_capacity'])
            else:
                tank_size = int(tank_sizes[category_short_eu])
            category_object: CarCategoryModel = query_category_for_category_short(category_short_eu=category_short_eu)
            if category_short_eu not in route_result:
                route_result[category_short_eu] = dict()
                route_result[category_short_eu]['total_emissions'] = dict()
                route_result[category_short_eu]['fuel_factors'] = dict()
                route_result[category_short_eu]['total_consumption'] = dict()
                route_result[category_short_eu]['total_cost'] = dict()
                route_result[category_short_eu]['route'] = dict()
                route_result[category_short_eu]['category_info'] = dict()
                route_result[category_short_eu]['category_info']['ec_sensors'] = fuel_model.number_sensors
                route_result[category_short_eu]['category_info']['ec_measurements'] = fuel_model.number_measurements
                route_result[category_short_eu]['category_info']['en'] = category_object.category_name_en
                route_result[category_short_eu]['category_info']['de'] = category_object.category_name_de
                route_result[category_short_eu]['category_info'][
                    'manual_consumption'] = True if manual_consumption_per_100_km is not None else False

            fuel_type = fuel_model.fuel_type
            liters: [float] or float = 0
            co2_gram: [float] or float = 0
            result_liter_100: [float] or float = 0
            result_co2_gram_per_km: [float] or float = 0
            cost_tax: [float] or float = 0
            cost_wo_tax: [float] or float = 0
            co2_gram_per_liter = 0
            cost_date: date = None
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
                fuel_calculation: FuelModelCalculationObject = fuel_model.calculate_route(kmh=self.average_speed,
                                                                                          length_m=length_m,
                                                                                          manual_consumption_per_100km=manual_consumption_per_100_km)

                result_fuel_liter_total = fuel_calculation.result_fuel_liter_total
                result_co2_gram_total = fuel_calculation.result_co2_gram_total
                co2_gram_per_liter = fuel_calculation.co2_gram_per_liter

                result_liter_100: [float] or float = fuel_calculation.liter_per_100_km
                result_co2_gram_per_km: [float] or float = fuel_calculation.co2_gram_per_km
                co2_gram_per_liter: [float] or float = co2_gram_per_liter
                co2_gram += result_co2_gram_total
                liters += result_fuel_liter_total
                if remaining_fuel > 0:
                    result_fuel_liter_total -= remaining_fuel
                    remaining_fuel = 0
                needed_refueling_theory = result_fuel_liter_total / tank_size
                needed_refueling_actual = math.ceil(needed_refueling_theory)
                if tank_size * needed_refueling_actual - result_fuel_liter_total > 0:
                    remaining_fuel = tank_size * needed_refueling_actual - result_fuel_liter_total

                price_calculation: LinePriceCalculationObject = price_model.calculate_category_cost(
                    liter=result_fuel_liter_total,
                    fuel_type=fuel_type)
                cost_date = price_calculation.cost_date
                cost_tax += price_calculation.fuel_cost_tax
                cost_wo_tax += price_calculation.fuel_cost_wo_tax

            route_result[category_short_eu]['route']['km'] = round(total_km[0] if type(
                total_km) == ndarray else total_km, 6)

            route_result[category_short_eu]['total_consumption']['liters'] = round(liters[0] if type(
                liters) == ndarray else liters, 3)

            route_result[category_short_eu]['total_cost']['w_tax_euro'] = round(cost_tax[0] if type(
                cost_tax) == ndarray else cost_tax, 2)
            route_result[category_short_eu]['total_cost']['wo_tax_euro'] = round(cost_wo_tax[0] if type(
                cost_wo_tax) == ndarray else cost_wo_tax, 2)
            route_result[category_short_eu]['total_cost']['price_date'] = cost_date.strftime('%Y-%m-%dT%H:%M:%S')

            route_result[category_short_eu]['total_emissions']['co2_kg'] = round(co2_gram[0] / 1000 if type(
                co2_gram) == ndarray else co2_gram / 1000, 6)

            route_result[category_short_eu]['fuel_factors']['liter_per_100km'] = round(result_liter_100[0] if type(
                result_liter_100) == ndarray else result_liter_100, 1)
            route_result[category_short_eu]['fuel_factors']['co2_gram_per_km'] = round(
                result_co2_gram_per_km[0] if type(
                    result_co2_gram_per_km) == ndarray else result_co2_gram_per_km, 6)
            route_result[category_short_eu]['fuel_factors']['co2_gram_per_liter'] = round(co2_gram_per_liter[0] if type(
                co2_gram_per_liter) == ndarray else co2_gram_per_liter, 6)
        for category in vehicle_categories:
            if category not in route_result:
                route_result[category] = dict()
                route_result[category]['category_info'] = dict()
                route_result[category]['category_info']['en'] = vehicle_categories[category]['en']
                route_result[category]['category_info']['de'] = vehicle_categories[category]['de']
                route_result[category]['category_info'][
                    'calculation_errors'] = 'Not enough data to calculate the Category'
        return route_result


class FuelModelCalculationObject(object):
    def __init__(self):
        self.result_fuel_liter_total = None
        self.result_co2_gram_total = None
        self.liter_per_100_km = None
        self.co2_gram_per_km = None
        self.co2_gram_per_liter = None


class FuelModel(object):
    def __init__(self, category_statistics: list) -> None:
        co2_statistic: EnvirocarAverageVehicleTypeStatisticModel or EnvirocarAverageCategoryStatisticsModel = None
        consumption_statistic: EnvirocarAverageVehicleTypeStatisticModel or EnvirocarAverageCategoryStatisticsModel = None
        speed_statistic: EnvirocarAverageVehicleTypeStatisticModel or EnvirocarAverageCategoryStatisticsModel = None
        self.fuel_type: str = None
        self.number_sensors: int = None
        self.number_measurements: int = None
        self.fuel_co2_gram_emission = 2392
        self.diesel_co2_gram_emission = 2640
        self.category_short_eu: str = None
        for statistic in category_statistics:
            if statistic.phenomenon_name == 'CO2':
                co2_statistic = statistic
                self.fuel_type = statistic.fuel_type
                self.number_sensors = statistic.numb_sensors
                self.number_measurements = statistic.measurements
                if type(statistic) == EnvirocarAverageCategoryStatisticsModel:
                    self.category_short_eu = statistic.category_short_eu
                pass
            elif statistic.phenomenon_name == 'Consumption':
                consumption_statistic = statistic
                pass
            elif statistic.phenomenon_name == 'Speed':
                speed_statistic = statistic
                pass
        self.average_tank_capacity: int = vehicle_categories[self.category_short_eu]['tank_capacity']
        self.co2_unit: str = co2_statistic.ec_phenomenons.unit
        self.consumption_unit: str = consumption_statistic.ec_phenomenons.unit
        self.speed_unit: str = speed_statistic.ec_phenomenons.unit
        self.co2_min: Decimal = co2_statistic.min
        self.co2_average: Decimal = co2_statistic.average
        self.co2_max: Decimal = co2_statistic.max
        self.consumption_min: Decimal = consumption_statistic.min
        self.consumption_average: Decimal = consumption_statistic.average
        self.consumption_max: Decimal = consumption_statistic.max
        self.speed_min: Decimal = 0
        self.speed_average: Decimal = speed_statistic.average
        self.speed_max: Decimal = speed_statistic.max
        self.liter_per_km = 0
        self.co2_per_liter = 0

    def calculate_route(self, kmh: int, length_m: float,
                        manual_consumption_per_100km: float = None) -> FuelModelCalculationObject:
        return FuelModelCalculationObject()

    def get_consumption_growth_factor(self, start_speed, dest_speed):
        pass


class EnvirocarFuelModel(FuelModel):
    def __init__(self, category_statistics: list):
        super().__init__(category_statistics=category_statistics)

    def calculate_route(self, kmh: int, length_m: float,
                        manual_consumption_per_100km: float = None) -> FuelModelCalculationObject:
        kmh = int(kmh)
        length_km = length_m * 0.0010000
        speed_per_hour: [] = [float(self.speed_min), float(self.speed_average), float(self.speed_max)]
        consumption_per_hour: [] = [float(self.consumption_min),
                                    float(self.consumption_average),
                                    float(self.consumption_max)]
        co2_per_hour: [] = [float(self.co2_min), float(self.co2_average), float(self.co2_max)]

        interpolation_consumption = interp1d(speed_per_hour, consumption_per_hour, kind='quadratic',
                                             bounds_error=False,
                                             fill_value='interpolate')
        self.liter_for_kmh = interpolation_consumption(kmh)

        if manual_consumption_per_100km is None:
            self.liter_per_km = self.liter_for_kmh / kmh
        else:
            self.liter_per_km = (manual_consumption_per_100km / 100)
        interpolation_co2 = interp1d(speed_per_hour, co2_per_hour, kind='quadratic', bounds_error=False,
                                     fill_value='interpolate')

        self.co2_kg_for_kmh = interpolation_co2(kmh)
        self.co2_kg_per_m = self.co2_kg_for_kmh / kmh
        self.co2_gram_per_km = self.co2_kg_per_m * 1000
        co2_gram_per_liter = self.co2_gram_per_km / self.liter_per_km

        liter_per_100_km = self.liter_per_km * 100
        if self.fuel_type == 'gasoline' and co2_gram_per_liter > self.fuel_co2_gram_emission:
            self.co2_gram_per_liter: int = self.fuel_co2_gram_emission
        elif self.fuel_type == 'diesel' and co2_gram_per_liter > self.diesel_co2_gram_emission:
            self.co2_gram_per_liter: int = self.diesel_co2_gram_emission
        else:
            self.co2_gram_per_liter = co2_gram_per_liter

        result_fuel_liter_total: float = length_km * self.liter_per_km
        result_co2_gram_total: float = length_km * self.co2_gram_per_km

        calculation_object = FuelModelCalculationObject()
        calculation_object.result_fuel_liter_total = result_fuel_liter_total
        calculation_object.result_co2_gram_total = result_co2_gram_total
        calculation_object.liter_per_100_km = liter_per_100_km
        calculation_object.co2_gram_per_km = self.co2_gram_per_km
        calculation_object.co2_gram_per_liter = self.co2_gram_per_liter
        return calculation_object

    def extrap1d(self, interpolator):
        xs = interpolator.x
        ys = interpolator.y

        def pointwise(x):
            if x < xs[0]:
                return ys[0] + (x - xs[0]) * (ys[1] - ys[0]) / (xs[1] - xs[0])
            elif x > xs[-1]:
                return ys[-1] + (x - xs[-1]) * (ys[-1] - ys[-2]) / (xs[-1] - xs[-2])
            else:
                return interpolator(x)

        def ufunclike(xs):
            return array(map(pointwise, array(xs)))

        return ufunclike

    def get_consumption_growth_factor(self, start_speed: int, dest_speed: int):
        """
        Returns the consumption growth factor for the consumption per kilometer as float.
        :param start_speed:
        :param dest_speed:
        """
        dest_speed = int(dest_speed)
        start_speed = int(start_speed)
        speed_per_hour: [] = array([float(self.speed_min), float(self.speed_average), float(self.speed_max)])
        consumption_per_hour: [] = array([float(self.consumption_min),
                                          float(self.consumption_average),
                                          float(self.consumption_max)])
        co2_per_hour: [] = [float(self.co2_min), float(self.co2_average), float(self.co2_max)]

        interpolation = interp1d(speed_per_hour, consumption_per_hour, kind='quadratic',
                                 bounds_error=False, fill_value='extrapolate')

        interpolation_co2 = interp1d(speed_per_hour, co2_per_hour, kind='quadratic', bounds_error=False,
                                     fill_value='extrapolate')

        start_co2_kg_for_kmh = interpolation_co2(start_speed)
        if start_co2_kg_for_kmh < 0:
            start_co2_kg_for_kmh = 0
        end_co2_kg_for_kmh = interpolation_co2(dest_speed)
        if end_co2_kg_for_kmh < 0:
            end_co2_kg_for_kmh = 0
        start_co2_kg_for_km = start_co2_kg_for_kmh / start_speed
        if start_co2_kg_for_km < 0:
            start_co2_kg_for_km = 0
        end_co2_kg_for_km = end_co2_kg_for_kmh / dest_speed
        if end_co2_kg_for_km < 0:
            end_co2_kg_for_km = 0
        start_kmh_liter = interpolation(start_speed)
        dest_kmh_liter = interpolation(dest_speed)
        start_liter_per_km = start_kmh_liter / start_speed
        dest_liter_per_km = dest_kmh_liter / dest_speed
        if dest_liter_per_km <= 0:
            dest_liter_per_km = 0.00000001

        fuel_multiplicator = math.sqrt(dest_liter_per_km / start_liter_per_km) - 1
        co2_multiplicator = math.sqrt(end_co2_kg_for_km / start_co2_kg_for_km) - 1

        # factor2 = (dest_liter_per_km - start_liter_per_km) / start_liter_per_km
        return fuel_multiplicator, co2_multiplicator
