import datetime
import time
import uuid
from collections import OrderedDict
from itertools import product
from multiprocessing.dummy import Pool as ThreadPool

import pyexcel
import requests
import xlrd
from deepmerge import always_merger
from tqdm import tqdm

from openfuelservice.server import ofs_settings, temp_folder
from openfuelservice.server.db_import.hashes.import_hashes import import_hashes
from openfuelservice.server.db_import.hashes.objects import HashObject
from openfuelservice.server.utils.data_update.hash_functions import file_hash
from openfuelservice.server.utils.misc import file_management
from openfuelservice.server.utils.misc.data_types import string_to_float
from openfuelservice.server.utils.misc.file_management import file_from_zip, download_file, test_xls, copy_file_to_temp

eurostat_settings = ofs_settings['statistics_provider']['eurostat_oil_provider']
oil_weekly_url = eurostat_settings['oil_weekly_url']
oil_history_2005_url = eurostat_settings['oil_history_2005']['url']
oil_history_2005_sheets = eurostat_settings['oil_history_2005']['sheets']
oil_history_1994_file = eurostat_settings['oil_history_1994']['file']
oil_history_1994_dataset = eurostat_settings['oil_history_1994']['dataset']
oil_history_1994_dataset_mappings = eurostat_settings['oil_history_1994']['dataset_mappings']
cpu = ofs_settings['general']['cpu']


class Tools:
    @staticmethod
    def col_from_key(sheet, key):
        col_location = {}
        for row_index, col_index in product(range(sheet.nrows), range(sheet.ncols)):
            if sheet.cell(row_index, col_index).value == key:
                col_location['row'] = row_index
                col_location['col'] = col_index
                return col_location


class WeeklyOil:
    """Not implemented at the moment!"""
    @classmethod
    def fetch(cls, url):
        resp = requests.get(url)
        data = url.rsplit('/', 1)[-1]

        try:
            with open(data, 'wb') as output:
                output.write(resp.content)
        except Exception:
            pass

        if url.rsplit('.', 1)[-1] == 'xls':
            return data
        elif url.rsplit('.', 1)[-1] == 'xlsx':
            return ""
        else:
            return ""

    @staticmethod
    def process(xls):
        my_dict = pyexcel.get_dict(file_name=xls, name_columns_by_row=0)
        book_dict = pyexcel.get_book_dict(file_name=xls)
        records = pyexcel.get_records(file_name=xls)
        return book_dict

    def get(self):
        weekly = {}
        print("Crawl EUROSTAT weekly oil data")
        while True:
            start_time = time.time()
            weekly.update(self.process(self.fetch(oil_weekly_url)))
            end_time = time.time()
            break
        print("Crawl-Result: {} Weekly-Prices | {} Seconds".format(len(weekly), end_time - start_time))
        return weekly


class HistoryOil2005:
    country_prices = dict()
    general_prices = dict()

    @staticmethod
    def combine_country_values(country_prices):
        combined_prices = dict()
        for element in country_prices:
            if element == 'w_tax':
                for country in country_prices[element]:
                    temp_country_prices = dict()
                    for date_element in country_prices[element][country]:
                        date_data = country_prices[element][country][date_element]
                        temp_dict = dict()
                        temp_dict['taux'] = date_data['taux']
                        temp_dict['euro_price'] = date_data['euro_price']
                        temp_dict['euro_ttc'] = date_data['euro_super_95']
                        temp_dict['euro_unit'] = date_data['euro_unit']
                        temp_dict['euro_quantity'] = date_data['euro_quantity']
                        temp_dict['diesel_ttc'] = date_data['diesel']
                        temp_dict['diesel_unit'] = date_data['diesel_unit']
                        temp_dict['diesel_quantity'] = date_data['diesel_quantity']
                        temp_country_prices[date_element] = temp_dict
                    if country in country_prices:
                        combined_prices[country].update(temp_country_prices)
                    else:
                        combined_prices[country] = temp_country_prices
            if element == 'wo_tax':
                for country in country_prices[element]:
                    for date_element in country_prices[element][country]:
                        if country not in combined_prices:
                            combined_prices[country] = dict()
                        if country in combined_prices:
                            temp_country_prices = dict()
                            if date_element in combined_prices[country]:
                                date_data = country_prices[element][country][date_element]
                                combined_prices[country][date_element]['euro_ht'] = date_data['euro_super_95']
                                combined_prices[country][date_element]['diesel_ht'] = date_data['diesel']
                            else:
                                date_data = country_prices[element][country][date_element]
                                temp_dict = dict()
                                temp_dict['taux'] = date_data['taux']
                                temp_dict['euro_price'] = date_data['euro_price']
                                temp_dict['euro_ht'] = date_data['euro_super_95']
                                temp_dict['euro_unit'] = date_data['euro_unit']
                                temp_dict['euro_quantity'] = date_data['euro_quantity']
                                temp_dict['diesel_ht'] = date_data['diesel']
                                temp_dict['diesel_unit'] = date_data['diesel_unit']
                                temp_dict['diesel_quantity'] = date_data['diesel_quantity']
                                temp_country_prices[date_element] = temp_dict
        return combined_prices

    @staticmethod
    def combine_general_values(general_prices):
        combined_prices = dict()
        # No taux added here. Generalized data are not country sensitive anymore
        for element in general_prices:
            if element == 'w_tax':
                for date_element in general_prices[element]:
                    date_data = general_prices[element][date_element]
                    temp_dict = dict()
                    temp_dict['euro_price'] = date_data['euro_price']
                    temp_dict['euro_ttc'] = date_data['euro_super_95']
                    temp_dict['euro_unit'] = date_data['euro_unit']
                    temp_dict['euro_quantity'] = date_data['euro_quantity']
                    temp_dict['diesel_ttc'] = date_data['diesel']
                    temp_dict['diesel_unit'] = date_data['diesel_unit']
                    temp_dict['diesel_quantity'] = date_data['diesel_quantity']
                    if date_element in combined_prices:
                        combined_prices[date_element].update(temp_dict)
                    else:
                        combined_prices[date_element] = temp_dict
            if element == 'wo_tax':
                for date_element in general_prices[element]:
                    if date_element in combined_prices:
                        date_data = general_prices[element][date_element]
                        combined_prices[date_element]['euro_ht'] = date_data['euro_super_95']
                        combined_prices[date_element]['diesel_ht'] = date_data['diesel']
                    else:
                        combined_prices[date_element] = dict()
                        date_data = general_prices[date_element]
                        temp_prices = dict()
                        temp_dict = dict()
                        temp_dict['euro_price'] = date_data['euro_price']
                        temp_dict['euro_ht'] = date_data['euro_super_95']
                        temp_dict['euro_unit'] = date_data['euro_unit']
                        temp_dict['euro_quantity'] = date_data['euro_quantity']
                        temp_dict['diesel_ht'] = date_data['diesel']
                        temp_dict['diesel_unit'] = date_data['diesel_unit']
                        temp_dict['diesel_quantity'] = date_data['diesel_quantity']
                        temp_prices[date_element] = temp_dict
        return combined_prices

    @classmethod
    def fetch(cls, url):
        xls_file = download_file(url)
        object_hash = file_hash(xls_file)
        if test_xls(xls_file):
            import_hashes(HashObject(
                uuid=uuid.uuid4().bytes,
                object_name=xls_file.name,
                object_hash=object_hash,
                hash_date=datetime.datetime.now()
            ))
            return xls_file
        else:
            return ""

    @classmethod
    def process_country(cls, country_package):
        package = country_package[1]
        sheet = package['sheet']
        sheet_name = package['sheet_name']
        row_number = package['row']
        code = package['code']
        datemode = package['datemode']
        unsorted_dict = dict()
        for row in range(sheet.nrows):
            row_code = sheet.cell_value(row, 0)
            if row > row_number:
                date = sheet.cell_value(row, 1)
                taux = sheet.cell_value(row, 2)
                euro_super = string_to_float(sheet.cell_value(row, 3).replace(',', ''))
                diesel = string_to_float(sheet.cell_value(row, 4).replace(',', ''))
                # taux is needed for history data values with foreign currencies
                # Here it is always set 1 because all values are in euro
                if row_code != code and row_code != "" or row >= sheet.nrows:
                    break
                if isinstance(date, float):
                    date_as_datetime = datetime.datetime(*xlrd.xldate_as_tuple(date, datemode)).date()
                    temporary_dict = dict()
                    temporary_dict['euro_super_95'] = euro_super
                    temporary_dict['diesel'] = diesel
                    temporary_dict['taux'] = taux
                    # This dataset only contains prices in euro
                    temporary_dict['euro_price'] = 1
                    temporary_dict['euro_unit'] = 'liter'
                    temporary_dict['euro_quantity'] = 1000
                    temporary_dict['diesel_unit'] = 'liter'
                    temporary_dict['diesel_quantity'] = 1000
                    unsorted_dict[date_as_datetime] = temporary_dict
            if row > row_number and row_code != code and row_code != "" or row >= sheet.nrows:
                break
        if sheet_name in cls.country_prices:
            prices = dict()
            prices[code] = OrderedDict(sorted(unsorted_dict.items(), key=lambda t: t[0]))
            cls.country_prices[sheet_name].update(prices)
        else:
            prices = dict()
            prices[code] = OrderedDict(sorted(unsorted_dict.items(), key=lambda t: t[0]))
            cls.country_prices[sheet_name] = prices

    @staticmethod
    def process_general(sheet, datemode):
        unsorted_dict = dict()
        # No taux added here. Generalized data are not country sensitive anymore.
        for row in range(sheet.nrows):
            date = sheet.cell_value(row, 1)
            euro_super = sheet.cell_value(row, 2)
            diesel = sheet.cell_value(row, 3)
            if isinstance(date, float):
                date_as_datetime = datetime.datetime(*xlrd.xldate_as_tuple(date, datemode)).date()
                temporary_dict = dict()
                temporary_dict['euro_super_95'] = euro_super
                temporary_dict['diesel'] = diesel
                temporary_dict['euro_price'] = 1
                temporary_dict['euro_unit'] = 'liter'
                temporary_dict['euro_quantity'] = 1000
                temporary_dict['diesel_unit'] = 'liter'
                temporary_dict['diesel_quantity'] = 1000
                unsorted_dict[date_as_datetime] = temporary_dict
        return OrderedDict(sorted(unsorted_dict.items(), key=lambda t: t[0]))

    @classmethod
    def process(cls, xls, country_codes):
        prices = dict()
        wb = xlrd.open_workbook(xls, on_demand=True)
        country_sheets = oil_history_2005_sheets['country']
        general_sheets = oil_history_2005_sheets['eu_general']
        for sheet_name in country_sheets:
            sheet = wb.sheet_by_name(country_sheets[sheet_name])
            country_packages = dict()
            for row in range(sheet.nrows):
                code = sheet.cell_value(row, 0)
                for country_code in country_codes:
                    if code == '':
                        pass
                    elif code == country_codes[country_code]['ISO3166-1-Alpha-2'] or code == \
                            country_codes[country_code][
                                'ISO3166-1-Alpha-3']:
                        country_package = dict()
                        country_package['row'] = row
                        country_package['sheet'] = sheet
                        country_package['sheet_name'] = sheet_name
                        country_package['datemode'] = wb.datemode
                        country_package['code'] = code
                        country_packages[code] = country_package
                    else:
                        pass
            with ThreadPool(cpu) as pool:
                for _ in tqdm(pool.imap_unordered(cls.process_country, country_packages.items()),
                              total=len(country_packages), unit=' Processing Country Fuel Prices'):
                    pass

        for sheet_name in general_sheets:
            sheet = wb.sheet_by_name(general_sheets[sheet_name])
            general_prices = cls.process_general(sheet, wb.datemode)
            if sheet_name in cls.general_prices:
                cls.general_prices[sheet_name].update(OrderedDict(sorted(general_prices.items(), key=lambda t: t[0])))
            else:
                cls.general_prices[sheet_name] = OrderedDict(sorted(general_prices.items(), key=lambda t: t[0]))

        prices['country_prices'] = cls.combine_country_values(cls.country_prices)
        prices['general_prices'] = cls.combine_general_values(cls.general_prices)
        return prices

    def get(self, country_codes):
        history = {}
        print("Crawl EUROSTAT-OIL history after 2005")
        while True:
            start_time = time.time()
            history.update(self.process(self.fetch(oil_history_2005_url), country_codes))
            end_time = time.time()
            break
        print("Crawl-Result: {} History-Price-Sets since 2005 | {} Seconds".format(len(history), end_time - start_time))
        return history


class HistoryOil1994:
    country_prices = dict()

    @classmethod
    def fetch(cls, zip_file):
        import_hashes(HashObject(
            uuid=uuid.uuid4().bytes,
            object_name=zip_file.name,
            object_hash=file_hash(zip_file),
            hash_date=datetime.datetime.now()
        ))
        return file_from_zip(oil_history_1994_dataset, zip_file)

    @staticmethod
    def process_mean(temp_prices):
        general_prices = dict()
        for country in temp_prices:
            for date in temp_prices[country]:
                # Checks if the same date exists. If so, it calculates the simple mean of both
                # No taux added here. Generalized data are not country sensitive anymore
                if date in general_prices:
                    euro_price = temp_prices[country][date]['euro_price']
                    taux = temp_prices[country][date]['taux']
                    euro_ht = temp_prices[country][date]['euro_ht']
                    euro_ttc = temp_prices[country][date]['euro_ttc']
                    diesel_ht = temp_prices[country][date]['diesel_ht']
                    diesel_ttc = temp_prices[country][date]['diesel_ttc']
                    general_prices[date] = dict()
                    # Add units
                    general_prices[date]['euro_unit'] = 'liter'
                    general_prices[date]['euro_quantity'] = 1000
                    general_prices[date]['diesel_unit'] = 'liter'
                    general_prices[date]['diesel_quantity'] = 1000
                    if euro_price == 1 or None:
                        if euro_ht is not None and euro_ht is not "":
                            if 'euro_ht' not in general_prices[date]:
                                general_prices[date]['euro_ht'] = euro_ht
                            else:
                                general_prices[date]['euro_ht'] = (general_prices[date]['euro_ht'] + euro_ht) / 2
                        if euro_ttc is not None and euro_ttc is not "":
                            if 'euro_ttc' not in general_prices[date]:
                                general_prices[date]['euro_ttc'] = euro_ttc
                            else:
                                general_prices[date]['euro_ttc'] = (general_prices[date]['euro_ttc'] + euro_ttc) / 2
                        if diesel_ht is not None and diesel_ht is not "":
                            if 'diesel_ht' not in general_prices[date]:
                                general_prices[date]['diesel_ht'] = diesel_ht
                            else:
                                general_prices[date]['diesel_ht'] = (general_prices[date]['diesel_ht'] + diesel_ht) / 2
                        if diesel_ttc is not None and diesel_ttc is not "":
                            if 'diesel_ttc' not in general_prices[date]:
                                general_prices[date]['diesel_ttc'] = diesel_ttc
                            else:
                                general_prices[date]['diesel_ttc'] = (general_prices[date][
                                                                          'diesel_ttc'] + diesel_ttc) / 2
                    if euro_price == 0:
                        if euro_ht is not None and euro_ht is not "":
                            if 'euro_ht' not in general_prices[date]:
                                general_prices[date]['euro_ht'] = euro_ht / taux
                            else:
                                general_prices[date]['euro_ht'] = (general_prices[date]['euro_ht'] + (
                                        euro_ht / taux)) / 2
                        if euro_ttc is not None and euro_ttc is not "":
                            if 'euro_ttc' not in general_prices[date]:
                                general_prices[date]['euro_ttc'] = euro_ttc / taux
                            else:
                                general_prices[date]['euro_ttc'] = (general_prices[date]['euro_ttc'] + (
                                        euro_ttc / taux)) / 2
                        if diesel_ht is not None and diesel_ht is not "":
                            if 'diesel_ht' not in general_prices[date]:
                                general_prices[date]['diesel_ht'] = diesel_ht / taux
                            else:
                                general_prices[date]['diesel_ht'] = (general_prices[date]['diesel_ht'] + (
                                        diesel_ht / taux)) / 2
                        if diesel_ttc is not None and diesel_ttc is not "":
                            if 'diesel_ttc' not in general_prices[date]:
                                general_prices[date]['diesel_ttc'] = diesel_ttc / taux
                            else:
                                general_prices[date]['diesel_ttc'] = (general_prices[date]['diesel_ttc'] + (
                                        diesel_ttc / taux)) / 2
                    general_prices[date]['euro_price'] = 1

                # Just add the date object. No mean necessary here!
                if date not in general_prices:
                    # Add units
                    general_prices[date] = dict()
                    euro_price = temp_prices[country][date]['euro_price']
                    taux = temp_prices[country][date]['taux']
                    general_prices[date]['euro_unit'] = 'liter'
                    general_prices[date]['euro_quantity'] = 1000
                    general_prices[date]['diesel_unit'] = 'liter'
                    general_prices[date]['diesel_quantity'] = 1000
                    # Add Values
                    euro_ht = temp_prices[country][date]['euro_ht']
                    euro_ttc = temp_prices[country][date]['euro_ttc']
                    diesel_ht = temp_prices[country][date]['diesel_ht']
                    diesel_ttc = temp_prices[country][date]['diesel_ttc']
                    if euro_price == 1 or None:
                        general_prices[date]['euro_price'] = euro_price
                        general_prices[date]['taux'] = 1
                        if euro_ht is not None and euro_ht is not "":
                            general_prices[date]['euro_ht'] = euro_ht
                        if euro_ttc is not None and euro_ttc is not "":
                            general_prices[date]['euro_ttc'] = euro_ttc
                        if diesel_ht is not None and diesel_ht is not "":
                            general_prices[date]['diesel_ht'] = diesel_ht
                        if diesel_ttc is not None and diesel_ttc is not "":
                            general_prices[date]['diesel_ttc'] = diesel_ttc
                    if euro_price == 0:
                        general_prices[date]['euro_price'] = 1
                        general_prices[date]['taux'] = 1
                        if euro_ht is not None and euro_ht is not "":
                            general_prices[date]['euro_ht'] = euro_ht / taux
                        if euro_ttc is not None and euro_ttc is not "":
                            general_prices[date]['euro_ttc'] = euro_ttc / taux
                        if diesel_ht is not None and diesel_ht is not "":
                            general_prices[date]['diesel_ht'] = diesel_ht / taux
                        if diesel_ttc is not None and diesel_ttc is not "":
                            general_prices[date]['diesel_ttc'] = diesel_ttc / taux
                    general_prices[date]['euro_price'] = 1

        return general_prices

    @classmethod
    def process(cls, xls, country_codes):
        prices = dict()
        temp_prices = dict()
        wb = xlrd.open_workbook(xls, on_demand=True)
        datemode = wb.datemode
        sheets = wb.sheets()
        # Access the sheet(s). The file just contains one sheet!
        for sheet in sheets:
            mappings_locations = {}
            for mapping in oil_history_1994_dataset_mappings:
                mappings_locations[mapping] = Tools.col_from_key(sheet, oil_history_1994_dataset_mappings[mapping])
            for row in tqdm(range(sheet.nrows), unit=' Processing Rows with Fuel prices'):
                # Get the row country id
                row_code = sheet.cell_value(row, mappings_locations.get('country_code').get('col'))
                # check against the eu country codes
                for country_code in country_codes:
                    if country_code == 'hashes':
                        pass
                    elif row_code == '':
                        pass
                    elif row_code == country_codes[country_code]['ISO3166-1-Alpha-2'] or row_code == \
                            country_codes[country_code]['ISO3166-1-Alpha-3']:
                        temp_values = dict()
                        # Get the date as float
                        date = sheet.cell_value(row, mappings_locations.get('date').get('col'))
                        # Convert it to a date object using the workbook datemode
                        date_as_datetime = datetime.datetime(*xlrd.xldate_as_tuple(date, datemode)).date()
                        taux = sheet.cell_value(row, mappings_locations.get('taux').get('col'))
                        euro_price = sheet.cell_value(row, mappings_locations.get('euro_price').get('col'))
                        euro_ht = sheet.cell_value(row, mappings_locations.get('euro_ht').get('col'))
                        if euro_ht == "":
                            euro_ht = 0
                        euro_ttc = sheet.cell_value(row, mappings_locations.get('euro_ttc').get('col'))
                        if euro_ttc == "":
                            euro_ttc = 0
                        diesel_ht = sheet.cell_value(row, mappings_locations.get('diesel_ht').get('col'))
                        if diesel_ht == "":
                            diesel_ht = 0
                        diesel_ttc = sheet.cell_value(row, mappings_locations.get('diesel_ttc').get('col'))
                        if diesel_ttc == "":
                            diesel_ttc = 0
                        if euro_price == 0:
                            temp_values['euro_price'] = 1
                            temp_values['taux'] = taux
                            temp_values['euro_ht'] = euro_ht / taux
                            temp_values['euro_ttc'] = euro_ttc / taux
                            temp_values['diesel_ht'] = diesel_ht / taux
                            temp_values['diesel_ttc'] = diesel_ttc / taux
                        else:
                            temp_values['euro_price'] = 1
                            temp_values['taux'] = taux
                            temp_values['euro_ht'] = euro_ht
                            temp_values['euro_ttc'] = euro_ttc
                            temp_values['diesel_ht'] = diesel_ht
                            temp_values['diesel_ttc'] = diesel_ttc
                        temp_values['euro_unit'] = 'liter'
                        temp_values['euro_quantity'] = 1000
                        temp_values['diesel_unit'] = 'liter'
                        temp_values['diesel_quantity'] = 1000
                        temp_date_object = dict()
                        temp_date_object[date_as_datetime] = temp_values
                        if row_code in temp_prices:
                            temp_prices[row_code].update(temp_date_object)
                        else:
                            temp_prices[row_code] = dict()
                            temp_prices[row_code] = temp_date_object
        prices['country_prices'] = temp_prices
        prices['general_prices'] = cls.process_mean(temp_prices)
        return prices

    def get(self, country_codes):
        history = {}
        oil_history_1994_zip = copy_file_to_temp(oil_history_1994_file)
        print("Process EUROSTAT-OIL history 1994 - 2005")
        while True:
            start_time = time.time()
            history.update(self.process(self.fetch(oil_history_1994_zip), country_codes))
            end_time = time.time()
            break
        print(
            "Crawl-Result: {} History-Price-Sets 1994 - 2005 | {} Seconds".format(len(history), end_time - start_time))
        return history


class ESData:
    def __init__(self, all_parameters: bool = False, history1994: bool = False, history2005: bool = False):
        """
        Initializes ESData to tell get what data will be needed.

        :param all_parameters: Set True to get all data sets
        :param history1994: Set True to get History between 1994 and 2005
        :param history2005: Set True to get History between after 2005
        """
        self.all_parameters = all_parameters
        if all_parameters:
            self.history1994 = True
            self.history2005 = True
        else:
            self.history1994 = history1994
            self.history2005 = history2005

    def get(self, country_codes: dict) -> dict:
        """
        The function works as a intermidiate function to get all the Eurostat data at once.

        :param country_codes: Provide a legit CounryObject holding the country codes
        :return: A dictonary holding the desired Eurostat data
        :rtype: dict
        """
        es_data = dict()
        """
        The function works as the entry point to get the data from EUROSTAT.
        First it checks if the temp folder is empty by either deleting it and/or creating a new and emptry one.
        :return: EUROSTAT oil data set with values ranging from 1994 till today.
        """
        file_management.create_directory(temp_folder)
        file_management.clean_directory(temp_folder)
        if self.history1994 and self.history2005 is False:
            es_data.update(HistoryOil1994().get(country_codes=country_codes))
        elif self.history2005 and self.history1994 is False:
            es_data.update(HistoryOil2005().get(country_codes=country_codes))
        elif self.history1994 and self.history2005:
            history1994 = HistoryOil1994().get(country_codes=country_codes)
            history2005 = HistoryOil2005().get(country_codes=country_codes)
            es_data.update(always_merger.merge(history1994, history2005))
        return es_data
