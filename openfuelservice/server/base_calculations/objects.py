from datetime import date

from geoalchemy2.shape import to_shape
from geopy.distance import geodesic
from shapely.geometry import LineString, Point

from openfuelservice.server.base_calculations.queries import query_general_price, query_country_price_by_linestring
from openfuelservice.server.db_import.eurostat.objects import CountryPrice, GeneralPrice, CountryPriceExtended
from openfuelservice.server.objects import Filters
from openfuelservice.server.utils.misc.geometries import true_linestring_length


def parse_price_model(line_string: LineString) -> []:
    prices: list = []
    cpe_list: list = query_country_price_by_linestring(linestring=line_string)
    gpo: GeneralPrice = query_general_price()
    country_price_extended: CountryPriceExtended
    # TODO 1. Line poly intersection 2. Create CountryLinePrice Object 3. Append to result 4. Get remaining Points by difference 5. Add GPo to them
    # 6. Revise calculation!
    remaining_linestring: LineString = line_string

    for country_price_extended in cpe_list:
        country_geom = to_shape(country_price_extended.geom)
        intersecting_route_part = country_geom.intersection(line_string)
        remaining_linestring = remaining_linestring.difference(intersecting_route_part)
        prices.append(CountryLinePrice(
            linestring=intersecting_route_part,
            country_price=country_price_extended.get_country_price_object()
        ))
    if remaining_linestring.length > 0:
        prices.append(GeneralLinePrice(
            linestring=remaining_linestring,
            general_price=gpo
        ))
    return prices


class Route(object):
    def __init__(self, geom: LineString, filters: Filters):
        """
        Initializes the basic calculation object. From it the route costs will be calculated.
        It sets the fuel type and vehicle type to predefined standards when not set in filters.

        :param geom: A valid shapely LineString
        :param filters: A dict holding the processing filters
        """
        self.geom: LineString = geom
        self.filters: Filters = filters
        self.categories: [] = filters.vehicle_categories
        self.price_models: [CountryLinePrice or GeneralLinePrice] = parse_price_model(self.geom)
        self.route_length = true_linestring_length(linestring=self.geom)
        self.fuel_models = None


class LinePriceCalculationObject(object):
    def __init__(self):
        self.fuel_cost_tax = None
        self.fuel_cost_wo_tax = None
        self.cost_date = None


class LinePrice(object):
    def __init__(self, linestring: LineString):
        self.linestring: LineString = linestring

    def calculate_cost(self, liter: float, fuel_type: str) -> LinePriceCalculationObject:
        return LinePriceCalculationObject()


class CountryLinePrice(LinePrice):
    def __init__(self, linestring: LineString, country_price: CountryPrice):
        super().__init__(linestring=linestring)
        self.country_price = country_price

    def calculate_cost(self, liter: float, fuel_type: object) -> LinePriceCalculationObject:
        fuel_cost_tax = 0
        fuel_cost_wo_tax = 0
        cost_date = self.country_price.date
        if fuel_type == 'gasoline':
            gasoline_price_tax = float(self.country_price.euro_ttc)
            gasoline_price_wo_tax = float(self.country_price.euro_ht)
            fuel_cost_tax = gasoline_price_tax * liter
            fuel_cost_wo_tax = gasoline_price_wo_tax * liter
            pass
        elif fuel_type == 'diesel':
            diesel_price_tax = float(self.country_price.diesel_ttc)
            diesel_price_wo_tax = float(self.country_price.diesel_ht)
            fuel_cost_tax = diesel_price_tax * liter
            fuel_cost_wo_tax = diesel_price_wo_tax * liter
        line_price_object = LinePriceCalculationObject()
        line_price_object.fuel_cost_wo_tax = fuel_cost_wo_tax
        line_price_object.fuel_cost_tax = fuel_cost_tax
        line_price_object.cost_date = cost_date
        return line_price_object


class GeneralLinePrice(LinePrice):
    def __init__(self, linestring: LineString, general_price: GeneralPrice):
        super().__init__(linestring=linestring)
        self.general_price = general_price

    def calculate_cost(self, liter, fuel_type) -> LinePriceCalculationObject:
        fuel_cost_tax = 0
        fuel_cost_wo_tax = 0
        cost_date = self.general_price.date
        if fuel_type == 'gasoline':
            gasoline_price_tax = float(self.general_price.euro_ttc)
            gasoline_price_wo_tax = float(self.general_price.euro_ht)
            fuel_cost_tax = gasoline_price_tax * liter
            fuel_cost_wo_tax = gasoline_price_wo_tax * liter
            pass
        elif fuel_type == 'diesel':
            diesel_price_tax = float(self.general_price.diesel_ttc)
            diesel_price_wo_tax = float(self.general_price.diesel_ht)
            fuel_cost_tax = diesel_price_tax * liter
            fuel_cost_wo_tax = diesel_price_wo_tax * liter
        line_price_object = LinePriceCalculationObject()
        line_price_object.fuel_cost_wo_tax = fuel_cost_wo_tax
        line_price_object.fuel_cost_tax = fuel_cost_tax
        line_price_object.cost_date = cost_date
        return line_price_object


class PointPriceCollection(object):
    def __init__(self):
        self.point_price_collection = []
        self.country_prices = []


class PointPrice(object):
    def __init__(self, point: Point, previous_point: Point):
        self.point: Point = point
        self.previous_point: Point = previous_point
        self.distance_to_previous: float = self.calculate_distance(point1=previous_point, point2=point)

    @staticmethod
    def calculate_distance(point1: Point, point2: Point) -> float:
        distance: float = geodesic((point1.y, point1.x), (point2.y, point2.x)).meters
        return distance

    def calculate_cost(self, liter, fuel_type) -> float and float and date:
        return float, float, date


class CountryPointPrice(PointPrice):
    def __init__(self, point: Point, previous_point: Point, country_price: CountryPrice):
        super().__init__(point=point, previous_point=previous_point)
        self.country_price: CountryPrice = country_price

    def calculate_cost(self, liter: float, fuel_type: object) -> float and float and date:
        fuel_cost_tax = 0
        fuel_cost_wo_tax = 0
        cost_date = self.country_price.date
        if fuel_type == 'gasoline':
            gasoline_price_tax = float(self.country_price.euro_ttc)
            gasoline_price_wo_tax = float(self.country_price.euro_ht)
            fuel_cost_tax = gasoline_price_tax * liter
            fuel_cost_wo_tax = gasoline_price_wo_tax * liter
            pass
        elif fuel_type == 'diesel':
            diesel_price_tax = float(self.country_price.diesel_ttc)
            diesel_price_wo_tax = float(self.country_price.diesel_ht)
            fuel_cost_tax = diesel_price_tax * liter
            fuel_cost_wo_tax = diesel_price_wo_tax * liter
        return fuel_cost_tax, fuel_cost_wo_tax, cost_date


class GeneralPointPrice(PointPrice):
    def __init__(self, point: Point, previous_point: Point, general_price: GeneralPrice):
        super().__init__(point=point, previous_point=previous_point)
        self.general_price = general_price

    def calculate_cost(self, liter, fuel_type) -> float and float and date:
        fuel_cost_tax = 0
        fuel_cost_wo_tax = 0
        cost_date = self.general_price.date
        if fuel_type == 'gasoline':
            gasoline_price_tax = float(self.general_price.euro_ttc)
            gasoline_price_wo_tax = float(self.general_price.euro_ht)
            fuel_cost_tax = gasoline_price_tax * liter
            fuel_cost_wo_tax = gasoline_price_wo_tax * liter
            pass
        elif fuel_type == 'diesel':
            diesel_price_tax = float(self.general_price.diesel_ttc)
            diesel_price_wo_tax = float(self.general_price.diesel_ht)
            fuel_cost_tax = diesel_price_tax * liter
            fuel_cost_wo_tax = diesel_price_wo_tax * liter
        return fuel_cost_tax, fuel_cost_wo_tax, cost_date
