import csv
import time
from datetime import datetime

from openfuelservice.server import ofs_settings, temp_folder
from openfuelservice.server.db_import.agency_data.carfueldata.objects import CarFuelDataCarObject
from openfuelservice.server.drivers.misc_driver import WikiMatcher
from openfuelservice.server.utils.misc import file_management
from openfuelservice.server.utils.misc.data_handling import check_manufacturer

cfd_settings = ofs_settings['statistics_provider']['carfueldata_provider']


class LatestCars(object):
    def __init__(self):
        self.cfd_objects_list = list()

    @staticmethod
    def check_name_for_year(car_name: str) -> int or None:
        # Only with latest cars. The data before have no date object and seldom a year in its name
        import datetime
        now = datetime.datetime.now()
        max_year = int(now.year)
        min_year = 1980
        search_year = max_year
        while True:
            if search_year < min_year:
                return None
            elif str(search_year) in car_name:
                return search_year
            else:
                search_year -= 1

    def process_data(self, zip_file):
        files: [] = file_management.unzip_download(source_file_path=zip_file, destination_folder=temp_folder)
        for cs_file in files:
            if cs_file.name.rsplit('.', 1)[-1] == 'csv':
                with open(cs_file, encoding='cp1252') as f:
                    reader = csv.reader(f, dialect='excel')
                    header_row = reader.__next__()
                    header_mapping = {
                        'manufacturer': 'Manufacturer',
                        'model': 'Model',
                        'description': 'Description',
                        'transmission': 'Transmission',
                        'engine_capacity': 'Engine Capacity',
                        'fuel_type': 'Fuel Type',
                        'e_consumption_miles_per_kWh': 'Electric energy consumption Miles/kWh',
                        'e_consumption_wh_per_km': 'wh/km',
                        'maximum_range_km': 'Maximum range (Km)',
                        'maximum_range_miles': 'Maximum range (Miles)',
                        'metric_urban_cold': 'Metric Urban (Cold)',
                        'metric_extra_urban': 'Metric Extra-Urban',
                        'metric_combined': 'Metric Combined',
                        'imperial_urban_cold': 'Imperial Urban (Cold)',
                        'imperial_extra_urban': 'Imperial Extra-Urban',
                        'imperial_combined': 'Imperial Combined',
                        'co2_g_per_km': 'CO2 g/km',
                        'fuel_cost_6000_miles': 'Fuel Cost 6000 Miles',
                        'fuel_cost_12000_miles': 'Fuel Cost 12000 Miles',
                        'electricity_cost': 'Electricity cost ',
                        'total_cost_per_12000_miles': 'Total cost / 12000 miles',
                        'euro_standard': 'Euro Standard',
                        'noise_level_dB_a_': 'Noise Level dB(A)',
                        'emissions_co_mg_per_km': 'Emissions CO [mg/km]',
                        'thc_emissions_mg_per_km': 'THC Emissions [mg/km]',
                        'emissions_nox_mg_per_km': 'Emissions NOx [mg/km]',
                        'thc_plus_nox_emissions_mg_per_km': 'THC + NOx Emissions [mg/km]',
                        'particulates_no_mg_per_km': 'Particulates [No.] [mg/km]',
                        'rde_nox_urban': 'RDE NOx Urban',
                        'rde_nox_combined': 'RDE NOx Combined',
                        'date_of_change': 'Date of change'
                    }
                    headers = {
                        'manufacturer': None,
                        'model': None,
                        'description': None,
                        'transmission': None,
                        'engine_capacity': None,
                        'fuel_type': None,
                        'e_consumption_miles_per_kWh': None,
                        'e_consumption_wh_per_km': None,
                        'maximum_range_km': None,
                        'maximum_range_miles': None,
                        'metric_urban_cold': None,
                        'metric_extra_urban': None,
                        'metric_combined': None,
                        'imperial_urban_cold': None,
                        'imperial_extra_urban': None,
                        'imperial_combined': None,
                        'co2_g_per_km': None,
                        'fuel_cost_6000_miles': None,
                        'fuel_cost_12000_miles': None,
                        'electricity_cost': None,
                        'total_cost_per_12000_miles': None,
                        'euro_standard': None,
                        'noise_level_dB_a_': None,
                        'emissions_co_mg_per_km': None,
                        'thc_emissions_mg_per_km': None,
                        'emissions_nox_mg_per_km': None,
                        'thc_plus_nox_emissions_mg_per_km': None,
                        'particulates_no_mg_per_km': None,
                        'rde_nox_urban': None,
                        'rde_nox_combined': None,
                        'date_of_change': None
                    }
                    counter = 0
                    for h in header_row:
                        for d in header_mapping:
                            if h is not None and h is not '' and h in header_mapping[d]:
                                headers[d] = counter
                        counter += 1
                    value_ignore_list = ['', 'N/A']

                    for row in reader:
                        manufacturer = row[headers['manufacturer']]
                        real_manufacturer = check_manufacturer(manufacturer_to_check=manufacturer)
                        if real_manufacturer != "":
                            manufacturer = real_manufacturer
                            model_name = row[headers['model']]
                            description = row[headers['description']]
                            year: int = self.check_name_for_year(car_name=manufacturer + ' ' + model_name + ' ' + description)
                            date_of_change = datetime.strptime(row[headers['date_of_change']], '%d %B %Y') if headers[
                                                                                                                  'date_of_change'] not in value_ignore_list else None
                            year = int(date_of_change.year) if year is None else year
                            self.cfd_objects_list.append(CarFuelDataCarObject(
                                manufacturer=manufacturer,
                                model=model_name,
                                description=description,
                                transmission=row[headers['transmission']],
                                engine_capacity=row[headers['engine_capacity']] if headers[
                                                                                       'engine_capacity'] not in value_ignore_list else None,
                                fuel_type=row[headers['fuel_type']] if headers[
                                                                           'fuel_type'] not in value_ignore_list else None,
                                e_consumption_miles_per_kWh=float(row[headers['e_consumption_miles_per_kWh']]) if
                                headers[
                                    'e_consumption_miles_per_kWh'] is not None and
                                row[
                                    headers[
                                        'e_consumption_miles_per_kWh']] not in value_ignore_list else None,
                                e_consumption_wh_per_km=float(row[headers['e_consumption_wh_per_km']]) if headers[
                                                                                                              'e_consumption_wh_per_km'] is not None and
                                                                                                          row[headers[
                                                                                                              'e_consumption_wh_per_km']] not in value_ignore_list else None,
                                maximum_range_km=float(row[headers['maximum_range_km']]) if headers[
                                                                                                'maximum_range_km'] is not None and
                                                                                            row[headers[
                                                                                                'maximum_range_km']] not in value_ignore_list else None,
                                maximum_range_miles=float(row[headers['maximum_range_miles']]) if headers[
                                                                                                      'maximum_range_miles'] is not None and
                                                                                                  row[headers[
                                                                                                      'maximum_range_miles']] not in value_ignore_list else None,
                                metric_urban_cold=float(row[headers['metric_urban_cold']]) if headers[
                                                                                                  'metric_urban_cold'] is not None and
                                                                                              row[headers[
                                                                                                  'metric_urban_cold']] not in value_ignore_list else None,
                                metric_extra_urban=float(row[headers['metric_extra_urban']]) if headers[
                                                                                                    'metric_extra_urban'] is not None and
                                                                                                row[headers[
                                                                                                    'metric_extra_urban']] not in value_ignore_list else None,
                                metric_combined=float(row[headers['metric_combined']]) if headers[
                                                                                              'metric_combined'] is not None and
                                                                                          row[headers[
                                                                                              'metric_combined']] not in value_ignore_list else None,
                                imperial_urban_cold=float(row[headers['imperial_urban_cold']]) if headers[
                                                                                                      'imperial_urban_cold'] is not None and
                                                                                                  row[headers[
                                                                                                      'imperial_urban_cold']] not in value_ignore_list else None,
                                imperial_extra_urban=float(row[headers['imperial_extra_urban']]) if headers[
                                                                                                        'imperial_extra_urban'] is not None and
                                                                                                    row[headers[
                                                                                                        'imperial_extra_urban']] not in value_ignore_list else None,
                                imperial_combined=float(row[headers['imperial_combined']]) if headers[
                                                                                                  'imperial_combined'] is not None and
                                                                                              row[headers[
                                                                                                  'imperial_combined']] not in value_ignore_list else None,
                                co2_g_per_km=float(row[headers['co2_g_per_km']]) if headers[
                                                                                        'co2_g_per_km'] is not None and
                                                                                    row[headers[
                                                                                        'co2_g_per_km']] not in value_ignore_list else None,
                                fuel_cost_6000_miles=float(row[headers['fuel_cost_6000_miles']]) if headers[
                                                                                                        'fuel_cost_6000_miles'] is not None and
                                                                                                    row[headers[
                                                                                                        'fuel_cost_6000_miles']] not in value_ignore_list else None,
                                fuel_cost_12000_miles=float(row[headers['fuel_cost_12000_miles']]) if headers[
                                                                                                          'fuel_cost_12000_miles'] is not None and
                                                                                                      row[headers[
                                                                                                          'fuel_cost_12000_miles']] not in value_ignore_list else None,
                                electricity_cost=float(row[headers['electricity_cost']]) if headers[
                                                                                                'electricity_cost'] is not None and
                                                                                            row[headers[
                                                                                                'electricity_cost']] not in value_ignore_list else None,
                                total_cost_per_12000_miles=float(row[headers['total_cost_per_12000_miles']]) if headers[
                                                                                                                    'total_cost_per_12000_miles'] is not None and
                                                                                                                row[
                                                                                                                    headers[
                                                                                                                        'total_cost_per_12000_miles']] not in value_ignore_list else None,
                                euro_standard=str(row[headers['euro_standard']]) if headers[
                                                                                        'euro_standard'] is not None and
                                                                                    row[headers[
                                                                                        'euro_standard']] not in value_ignore_list else None,
                                noise_level_dB_a_=float(row[headers['noise_level_dB_a_']]) if headers[
                                                                                                  'noise_level_dB_a_'] is not None and
                                                                                              row[headers[
                                                                                                  'noise_level_dB_a_']] not in value_ignore_list else None,
                                emissions_co_mg_per_km=float(row[headers['emissions_co_mg_per_km']]) if headers[
                                                                                                            'emissions_co_mg_per_km'] is not None and
                                                                                                        row[headers[
                                                                                                            'emissions_co_mg_per_km']] not in value_ignore_list else None,
                                thc_emissions_mg_per_km=float(row[headers['thc_emissions_mg_per_km']]) if headers[
                                                                                                              'thc_emissions_mg_per_km'] is not None and
                                                                                                          row[headers[
                                                                                                              'thc_emissions_mg_per_km']] not in value_ignore_list else None,
                                emissions_nox_mg_per_km=float(row[headers['emissions_nox_mg_per_km']]) if headers[
                                                                                                              'emissions_nox_mg_per_km'] is not None and
                                                                                                          row[headers[
                                                                                                              'emissions_nox_mg_per_km']] not in value_ignore_list else None,
                                thc_plus_nox_emissions_mg_per_km=float(
                                    row[headers['thc_plus_nox_emissions_mg_per_km']]) if
                                headers['thc_plus_nox_emissions_mg_per_km'] is not None and row[
                                    headers['thc_plus_nox_emissions_mg_per_km']] not in value_ignore_list else None,
                                particulates_no_mg_per_km=float(row[headers['particulates_no_mg_per_km']]) if headers[
                                                                                                                  'particulates_no_mg_per_km'] is not None and
                                                                                                              row[
                                                                                                                  headers[
                                                                                                                      'particulates_no_mg_per_km']] not in value_ignore_list else None,
                                rde_nox_urban=float(row[headers['rde_nox_urban']]) if headers[
                                                                                          'rde_nox_urban'] is not None and
                                                                                      row[headers[
                                                                                          'rde_nox_urban']] not in value_ignore_list else None,
                                rde_nox_combined=float(row[headers['rde_nox_combined']]) if headers[
                                                                                                'rde_nox_combined'] is not None and
                                                                                            row[headers[
                                                                                                'rde_nox_combined']] not in value_ignore_list else None,
                                date_of_change=datetime.strptime(row[headers['date_of_change']], '%d %B %Y') if headers[
                                                                                                                    'date_of_change'] not in value_ignore_list else None,
                                year=year
                            ))

    def fetch_data(self):
        file_management.clean_directory(temp_folder)
        data_url = cfd_settings['links']['latest_data']
        data_file = file_management.download_file_with_name(url=data_url, file_name='latest_cfd_data.zip')
        self.process_data(zip_file=data_file)

    def get_data(self) -> []:
        start_time = time.time()
        print("Crawl Latest Car Fuel Data Objects")
        self.fetch_data()
        end_time = time.time()
        print("Crawl-Result: {} Car Fuel Data Objects | {} Seconds".format(self.cfd_objects_list.__sizeof__(),
                                                                           end_time - start_time))
        return self
