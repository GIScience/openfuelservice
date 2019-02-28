import json

import geojson
from flask import Blueprint, request, Response
from shapely.geometry import shape
from voluptuous import Required, MultipleInvalid, Optional, Schema, Any, ALLOW_EXTRA

from openfuelservice.server import api_exceptions
from openfuelservice.server import category_list
from openfuelservice.server.base_calculations import calculate_route
from openfuelservice.server.objects import Filters
from openfuelservice.server.utils.database.queries import get_brands, get_cars, Wikipedia, get_car_ids
from openfuelservice.server.utils.misc.data_handling import check_manufacturer

vehicle_categories = category_list['car_categories']

envirocar_filters = Schema({

    Optional('filters'): {
        Required('data_source', msg='Please provide the desired data source -> ec or cfd'): str,
        Required('fuel_type', msg='Please provide a fuel type e.g. diesel/gas'): str,
        Optional('vehicle_type', msg='Please provide a vehicle type e.g. car'): str,
        Optional('driving_speed', msg='Optionally provide an average driving speed'): str,
        Optional('driving_style', msg='Optionally provide a driving style. moderate > fast > aggressive'): str,
        Optional('fuel_consumptions', msg='Optionally provide a manual fuel consumption'): int,
        Optional('vehicle_categories', msg='Optionally provide vehicle categories'): [],
        Optional('tank_sizes', msg='Optionally provide vehicle tank size'): int,
        Optional('request_id', msg='Optionally provide a personal request id'): int

    }
}, extra=ALLOW_EXTRA)

cfd_filters = Schema({

    Optional('filters'): {
        Required('data_source', msg='Please provide the desired data source -> ec or cfd'): str,
        Required('fuel_type', msg='Please provide a fuel type e.g. diesel/gas'): str,
        Optional('fuel_consumptions', msg='Optionally provide a manual fuel consumption'): int,
        Optional('driving_speed', msg='Optionally provide an average driving speed'): str,
        Optional('vehicle_categories', msg='Optionally provide vehicle categories'): [],
        Optional('tank_sizes', msg='Optionally provide vehicle tank size'): int,
        Optional('request_id', msg='Optionally provide a personal request id'): int,
        Optional('year', msg='Optionally provide a year to calculate the statistics from there on'): int,
        Optional('cfd_ids', msg='Optionally provide cfd car id'): str

    }
}, extra=ALLOW_EXTRA)

geom_schema = Schema({
    Required('geojson', msg='Must be a geojson object'): object,

    Optional('ec_filters'): envirocar_filters or cfd_filters
}, extra=ALLOW_EXTRA)

schema = Schema({
    Required('request'): Required(Any('route'), msg='route missing from request'),

    Required('geometry'): geom_schema
}, extra=ALLOW_EXTRA)

main_blueprint = Blueprint('main', __name__, )


@main_blueprint.route('/fuel', methods=['GET'])
def basic_data():
    if request.method == 'GET':
        if 'request' in request.args and str(request.args['request']).strip() == 'brands':
            if 'source' not in request.args or str(request.args['source']).strip() == 'all':
                brands: dict = request_brands(wikicar_brands=True, envirocar_brands=True, carfueldata_brands=True)
            elif 'source' in request.args and str(request.args['source']).strip() == 'cfd':
                brands: dict = request_brands(wikicar_brands=False, envirocar_brands=False, carfueldata_brands=True)
            elif 'source' in request.args and str(request.args['source']).strip() == 'ec':
                brands: dict = request_brands(wikicar_brands=False, envirocar_brands=True, carfueldata_brands=False)
            elif 'source' in request.args and str(request.args['source']).strip() == 'wikicar':
                brands: dict = request_brands(wikicar_brands=True, envirocar_brands=False, carfueldata_brands=False)
            else:
                raise api_exceptions.InvalidUsage(status_code=500, error_code=5001,
                                                  message='Wrong or missing filter argument for brands')
            r = Response(json.dumps(brands, sort_keys=True), mimetype='application/json; charset=utf-8')
            return r
        elif 'request' in request.args and str(request.args['request']).strip() == 'cars' and 'source' in request.args:
            source = str(request.args['source']).strip()
            brand = str(request.args['brand']).strip()
            if source == 'cfd':
                cars = request_car_ids(brand=brand, source=source)
                r = Response(json.dumps(cars, sort_keys=True), mimetype='application/json; charset=utf-8')
                return r
            else:
                raise api_exceptions.InvalidUsage(status_code=500, error_code=5001,
                                                  message=("Source {} not supported.".format(source)))
        elif 'request' in request.args and str(request.args['request']).strip() == 'cars':
            if 'brand' in request.args and str(request.args['brand']).strip() is not '':
                brand = request.args['brand']
                real_manufacturer = check_manufacturer(brand)
                if real_manufacturer is not '':
                    cars: dict = request_cars(brand=real_manufacturer)
                    r = Response(json.dumps(cars, sort_keys=True), mimetype='application/json; charset=utf-8')
                    return r
                else:
                    raise api_exceptions.InvalidUsage(status_code=500, error_code=5001,
                                                      message=("Couldn't find any brand matching: {}".format(brand)))
            else:
                raise api_exceptions.InvalidUsage(status_code=500, error_code=5001,
                                                  message=("Couldn't find any cars for the request"))

        elif 'request' in request.args and str(request.args['request']).strip() == 'categories':
            categories = request_categories()
            r = Response(json.dumps(categories, sort_keys=True), mimetype='application/json; charset=utf-8')
            return r
        else:
            raise api_exceptions.InvalidUsage(status_code=500, error_code=5001)

    else:
        raise api_exceptions.InvalidUsage(status_code=500, error_code=5002)


@main_blueprint.route('/fuel', methods=['POST'])
def route():
    if request.method == 'POST':
        if 'request' in request.args and str(request.args['request']).strip() == 'route':
            if 'application/json' in request.headers['Content-Type'] and request.is_json:

                all_args = request.get_json(silent=True)

                if all_args is None:
                    raise api_exceptions.InvalidUsage(status_code=500, error_code=4000)

                try:
                    schema(all_args)
                except MultipleInvalid as error:
                    raise api_exceptions.InvalidUsage(status_code=500, error_code=4000, message=str(error))
                # query stats
                if all_args['request'] == 'list':
                    r = Response(mimetype='application/json; charset=utf-8')
                    return r
                if 'geometry' not in all_args:
                    raise api_exceptions.InvalidUsage(status_code=500, error_code=4002)

                if 'filters' not in all_args['geometry']:
                    raise api_exceptions.InvalidUsage(status_code=500, error_code=4001)

                if 'data_source' in all_args['geometry']['filters']:
                    if 'cfd' in all_args['geometry']['filters']['data_source']:
                        pass
                    elif 'ec' in all_args['geometry']['filters']['data_source']:
                        pass
                    else:
                        raise api_exceptions.InvalidUsage(status_code=500, error_code=4009,
                                                          message=str("Please provide a valid data source"))
                else:
                    raise api_exceptions.InvalidUsage(status_code=500, error_code=4009)

                if 'fuel_type' not in all_args['geometry']['filters']:
                    raise api_exceptions.InvalidUsage(status_code=500, error_code=4003)

                are_required_geom_present(all_args['geometry'])
                all_args['geometry'] = parse_geometries(all_args['geometry'])
                route: dict = request_route_calculation(all_args)
                r = Response(json.dumps(route, sort_keys=True), mimetype='application/json; charset=utf-8')
                return r
            else:
                raise api_exceptions.InvalidUsage(status_code=500, error_code=4006)
        else:
            raise api_exceptions.InvalidUsage(status_code=500, error_code=5001)
    else:
        raise api_exceptions.InvalidUsage(status_code=500, error_code=5002)


def request_categories():
    return_categories = {}
    categories: {} = Wikipedia().get_categories(ordered=True)
    return_categories['categories'] = categories
    return return_categories


def request_brands(carfueldata_brands: bool = False, wikicar_brands: bool = False,
                   envirocar_brands: bool = False) -> {}:
    return_brands = {}
    brands = get_brands(carfueldata=carfueldata_brands, wikicar=wikicar_brands, envirocar=envirocar_brands)
    return_brands['brands'] = sorted(set(brands))
    return return_brands


def request_cars(brand: str) -> {}:
    if brand is not None:
        return_cars = {}
        cars = get_cars(brand=brand)
        return_cars['cars'] = cars
        return return_cars


def request_car_ids(brand: str, source: str):
    cars = {}
    if brand is not None and source is not None:
        cars = get_car_ids(brand=brand, source=source)
    return cars


def request_route_calculation(all_args: dict) -> {}:
    # Prepare the data and filters
    geom = all_args['geometry']['geom']
    filters = all_args['geometry']['filters']
    filters = Filters(filters=filters)
    request_id = filters.request_id
    data_source = filters.data_source
    route: {} = calculate_route(geom=geom, filters=filters, data_source=data_source, request_id=request_id)
    return route


def parse_geometries(geometry):
    """
    Parses the geometries to geojson objects and checks them for validity.
    :param geometry: Request parameters from get or post request
    :return: returns processed request parameters
    """

    # parse geojson
    if 'geojson' in geometry:

        s = json.dumps(geometry['geojson'])
        # Convert to geojson.geometry
        try:
            g1 = geojson.loads(s)
        except ValueError as e:
            raise api_exceptions.InvalidUsage(status_code=500, error_code=4007, message=str(e))

        # Feed to shape() to convert to shapely.geometry.linestring.LineString
        # This will invoke its __geo_interface__ (https://gist.github.com/sgillies/2217756)
        try:
            g2 = shape(g1)
        except ValueError as e:
            raise api_exceptions.InvalidUsage(status_code=500, error_code=4007, message=str(e))

        # parse geom if valid
        geojson_obj = check_validity(g2)

        if geojson_obj.geom_type == 'LineString':
            pass
        else:
            # type not supported
            raise api_exceptions.InvalidUsage(error_code=4007,
                                              message='GeoJSON type {} not supported'.format(geojson_obj.geom_type),
                                              status_code=500)

        geometry['geom'] = geojson_obj

    return geometry


def are_required_geom_present(geometry):
    """
    Checks if enough geometry options are are present in request.
    :param geometry: Geometry parameters from  post request
    """
    if 'geojson' not in geometry:
        raise api_exceptions.InvalidUsage(status_code=500, error_code=4005)


def check_validity(geojson):
    """
    Checks if geojson is valid, throws exception otherwise.
    :param geojson: geojson object
    :return: will return the geo
    """
    if geojson.is_valid:
        return geojson
    else:
        raise api_exceptions.InvalidUsage(status_code=500, error_code=4007, message='{} {}'.format(
            "geojson", geojson.is_valid))
