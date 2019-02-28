import csv
import datetime
import io
import os
import time
import uuid
import zipfile

import shapefile

from openfuelservice.server import ofs_settings, temp_folder
from openfuelservice.server.db_import.hashes.import_hashes import import_hashes
from openfuelservice.server.db_import.hashes.objects import HashObject
from openfuelservice.server.utils.data_update.hash_functions import file_hash
from openfuelservice.server.utils.misc.file_management import copy_file_to_temp

country_codes_file = ofs_settings['general']['country_codes']
country_boundaries_zip = ofs_settings['general']['country_boundaries']['zip_file']
iso2_col = ofs_settings['general']['country_boundaries']['iso2_col']
iso3_col = ofs_settings['general']['country_boundaries']['iso3_col']


class CountryCodes:
    @classmethod
    def process_country_codes(cls, country_codes):
        countries = dict()
        country_codes_path = copy_file_to_temp(country_codes)
        import_hashes(HashObject(
            uuid=uuid.uuid4().bytes,
            object_name=country_codes,
            object_hash=file_hash(country_codes_path),
            hash_date=datetime.datetime.now()
        ))
        with open(country_codes_path, newline='', encoding='utf-8') as csvfile:

            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            headers = reader.__next__()
            columns = {}
            counter = 0
            for h in headers:
                if 'ISO3166-1-Alpha-2' in h or 'ISO3166-1-Alpha-3' in h \
                        or 'ISO3166-1-numeric' in h or 'ISO4217-currency_alphabetic_code' in h \
                        or 'ISO4217-currency_name' in h or 'CLDR display name' in h or 'official_name_en' in h:
                    columns[h] = counter
                counter += 1
            for row in reader:
                country_name_col, alpha_2, alpha_3, numeric, currency_code, currency_name = columns[
                                                                                                'CLDR display name'], \
                                                                                            columns[
                                                                                                'ISO3166-1-Alpha-2'], \
                                                                                            columns[
                                                                                                'ISO3166-1-Alpha-3'], \
                                                                                            columns[
                                                                                                'ISO3166-1-numeric'], \
                                                                                            columns[
                                                                                                'ISO4217-currency_alphabetic_code'], \
                                                                                            columns[
                                                                                                'ISO4217-currency_name']
                countries[row[country_name_col]] = dict()
                countries[row[country_name_col]]['ISO3166-1-Alpha-2'] = row[alpha_2]
                countries[row[country_name_col]]['ISO3166-1-Alpha-3'] = row[alpha_3]
                countries[row[country_name_col]]['ISO3166-1-numeric'] = row[numeric]
                countries[row[country_name_col]]['ISO4217-currency_alphabetic_code'] = row[currency_code]
                countries[row[country_name_col]]['ISO4217-currency_name'] = row[currency_name]
        return countries


class CountryCodesShapes:

    @classmethod
    def process_country_shapes(cls, zip_file, country_codes):
        # Prepare necessary variables
        dbfname, shpname, shxname, columns, counter, countries = "", "", "", {}, 0, dict()
        # Copy the zip file to the temp folder
        zip_file_path = copy_file_to_temp(zip_file)
        # Get file hash for update purposes
        import_hashes(HashObject(
            uuid=uuid.uuid4().bytes,
            object_name=zip_file,
            object_hash=file_hash(zip_file_path),
            hash_date=datetime.datetime.now()
        ))
        # Open the zip file
        ziped_shapes = zipfile.ZipFile(open(zip_file_path, 'rb'))
        # Get a list with all names
        namelist = ziped_shapes.namelist()
        # Search for the specific extensions in the names
        for name in namelist:
            if name.rsplit('.', 1)[-1] == 'dbf':
                dbfname = ziped_shapes.read(name)
            if name.rsplit('.', 1)[-1] == 'shp':
                shpname = ziped_shapes.read(name)
            if name.rsplit('.', 1)[-1] == 'shx':
                shxname = ziped_shapes.read(name)
        # Create the shapefile
        shape_file = shapefile.Reader(shp=io.BytesIO(shpname), dbf=io.BytesIO(dbfname), shx=io.BytesIO(shxname))
        headers = shape_file.fields
        for h in headers:
            column_name = h[0]
            if iso2_col == column_name or iso3_col == column_name:
                columns[column_name] = counter
            counter += 1
        shape_records = shape_file.shapeRecords()
        # Access the single shape_record objects
        for shape_record in shape_records:
            record = shape_record.record
            shape_iso_a2 = record[columns[iso2_col] - 1]
            shape_iso_a3 = record[columns[iso3_col] - 1]
            for country in country_codes:
                country_iso_a2 = country_codes[country]['ISO3166-1-Alpha-2']
                country_iso_a3 = country_codes[country]['ISO3166-1-Alpha-3']
                if shape_iso_a2 == country_iso_a2 or shape_iso_a3 == country_iso_a3:
                    if country in countries:
                        if 'geom' in country:
                            geom = shape_record.shape.__geo_interface__
                            countries[country]['geom']['coordinates'].update(geom['coordinates'])
                        pass
                    else:
                        countries[country] = dict()
                        countries[country] = country_codes[country]
                        geom = shape_record.shape.__geo_interface__
                        countries[country]['geom'] = geom

        if shape_file.shapeType != 5:
            print("Error. The files in {} do not contain Polygons".format(zip_file_path))
        return countries


class CountryData:
    def get(self):
        print("Process country data")
        while True:
            start_time = time.time()
            country_codes = CountryCodes().process_country_codes(country_codes_file)
            countries = CountryCodesShapes().process_country_shapes(country_boundaries_zip, country_codes)
            end_time = time.time()
            break
        print("Processing-Result: {} Country-Sets | {} Seconds".format(len(countries), end_time - start_time))
        return countries
