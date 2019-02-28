from openfuelservice.server import eurostat_attribution, carfueldata_attribution, envirocar_attribution, ofs_settings
from openfuelservice.server.base_calculations import envirocar, cfd
from openfuelservice.server.objects import Filters


def __init__():
    pass


def calculate_route(geom, filters: Filters, data_source: str = 'cfd', request_id: str = None) -> dict:
    return_dict = dict()
    driving_style = filters.driving_style
    return_dict['general'] = dict()
    return_dict['general']['fuel_type'] = filters.fuel_type
    return_dict['general']['manual_driving_speed'] = True if filters.driving_speed is not None else False
    return_dict['general']['average_driving_speed'] = filters.driving_speed if filters.driving_speed is not None else \
        ofs_settings['general']['advanced_settings']['average_speeds'][driving_style]
    return_dict['general']['vehicle_type'] = filters.vehicle_type
    return_dict['general']['vehicle_categories'] = filters.vehicle_categories
    return_dict['general']['data_source'] = filters.data_source
    if request_id is not None:
        return_dict['request_id'] = request_id
    if filters.year is not None:
        return_dict['general']['min_calculation_year'] = filters.year

    if data_source == 'ec' or data_source is None:
        result: dict = envirocar.AdvancedDistanceCalculation(geom=geom, filters=filters).calculate_cost()
        return_dict['fuel_stats'] = result

        return_dict['attributions'] = dict()
        return_dict['attributions']['price_data_attribution'] = eurostat_attribution
        return_dict['attributions']['ec_data_attribution'] = envirocar_attribution
        return return_dict
    elif data_source == 'cfd':
        if filters.cfd_ids is not None and len(filters.cfd_ids) > 0:
            result: dict = cfd.DistanceCalculation(geom=geom, filters=filters).calculate_individual_cfd_cost()
        else:
            result: dict = cfd.DistanceCalculation(geom=geom, filters=filters).calculate_category_cost()
        return_dict['fuel_stats'] = result

        return_dict['attributions'] = dict()
        return_dict['attributions']['price_data_attribution'] = eurostat_attribution
        return_dict['attributions']['cfd_data_attribution'] = carfueldata_attribution
        return_dict['attributions']['ec_data_attribution'] = envirocar_attribution
        return return_dict
