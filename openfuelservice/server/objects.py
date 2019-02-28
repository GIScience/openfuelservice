from openfuelservice.server import ofs_settings

standard_vehicle_type = ofs_settings['general']['advanced_settings']['vehicle_type']
standard_driving_style = ofs_settings['general']['advanced_settings']['driving_style']


class Filters(object):
    def __init__(self, filters: dict):
        self.year: int = None
        self.driving_speed: int = None
        self.request_id = None
        self.data_source: str = 'ec'
        self.fuel_consumptions: int = None
        self.fuel_type: str = 'gasoline'
        self.vehicle_type: str = standard_vehicle_type
        self.driving_style: str = standard_driving_style
        self.tank_sizes: dict = None
        self.vehicle_categories: [] = ['all']
        self.cfd_ids = None
        if 'year' in filters:
            self.year = filters['year']
        if 'driving_speed' in filters:
            self.driving_speed = filters['driving_speed']
        if 'fuel_type' in filters:
            self.fuel_type = filters['fuel_type']
        if 'data_source' in filters and len(filters['data_source']) > 0:
            self.data_source = filters['data_source']
        if 'request_id' in filters:
            self.request_id = filters['request_id']
        if 'vehicle_type' in filters:
            self.vehicle_type = filters['vehicle_type']
        if 'driving_style' in filters:
            self.driving_style = filters['driving_style']
        if 'fuel_consumptions' in filters:
            self.fuel_consumptions = filters['fuel_consumptions']
        if 'vehicle_categories' in filters:
            self.vehicle_categories = filters['vehicle_categories']
        if 'tank_sizes' in filters:
            self.tank_sizes = filters['tank_sizes']
        if 'cfd_ids' in filters:
            self.cfd_ids = filters['cfd_ids']
