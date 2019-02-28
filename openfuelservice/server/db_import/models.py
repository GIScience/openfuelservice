import logging

from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import ARRAY

from openfuelservice.server import db, misc_tables, cfd_tables, ec_tables, es_tables, wiki_car_table, \
    wiki_category_table, countries_table, hash_table

logger = logging.getLogger(__name__)


# ec_tables = ofs_settings['statistics_provider']['envirocar_provider']['table_names']
# ec_geom = ofs_settings['statistics_provider']['envirocar_provider']['geometry_column']
# es_tables = ofs_settings['statistics_provider']['eurostat_oil_provider']['table_names']
# misc_tables = ofs_settings['statistics_provider']['misc']['table_names']
# cfd_tables = ofs_settings['statistics_provider']['carfueldata_provider']['table_names']


class WikiCarPageTextModel(db.Model):
    __tablename__ = misc_tables['wikicar_page_texts']
    hash_id = db.Column(db.CHAR(length=32), primary_key=True, unique=True)
    wiki_name = db.Column(db.String, nullable=False, index=True)
    brand_name = db.Column(db.String, nullable=False, index=True)
    car_name = db.Column(db.String, nullable=False, index=True)
    page_language = db.Column(db.String, nullable=False, index=True)
    page_text = db.Column(db.String, nullable=True)
    category_short_eu = db.Column(db.String, db.ForeignKey(
        '{}.category_short_eu'.format(wiki_category_table)), nullable=True, index=True)


class CarfuelDataCarModel(db.Model):
    __tablename__ = cfd_tables['carfueldata_cars']
    logger.info('table name for carfueldata car models: {}'.format(__tablename__))
    hash_id = db.Column(db.CHAR(length=32), primary_key=True, unique=True)
    logger.info('table name for sensors: {}'.format(__tablename__))
    manufacturer = db.Column(db.String, nullable=False, index=True)
    model = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    transmission = db.Column(db.String, nullable=False)
    engine_capacity = db.Column(db.String, nullable=False)
    fuel_type = db.Column(db.String, nullable=False)
    e_consumption_miles_per_kWh = db.Column(db.Float, nullable=True)
    e_consumption_wh_per_km = db.Column(db.Float, nullable=True)
    maximum_range_km = db.Column(db.Float, nullable=True)
    maximum_range_miles = db.Column(db.Float, nullable=True)
    metric_urban_cold = db.Column(db.Float, nullable=True)
    metric_extra_urban = db.Column(db.Float, nullable=True)
    metric_combined = db.Column(db.Float, nullable=True)
    imperial_urban_cold = db.Column(db.Float, nullable=True)
    imperial_extra_urban = db.Column(db.Float, nullable=True)
    imperial_combined = db.Column(db.Float, nullable=True)
    co2_g_per_km = db.Column(db.Float, nullable=True)
    fuel_cost_6000_miles = db.Column(db.Float, nullable=True)
    fuel_cost_12000_miles = db.Column(db.Float, nullable=True)
    electricity_cost = db.Column(db.Float, nullable=True)
    total_cost_per_12000_miles = db.Column(db.Float, nullable=True)
    euro_standard = db.Column(db.String, nullable=True)
    noise_level_dB_a_ = db.Column(db.Float, nullable=True)
    emissions_co_mg_per_km = db.Column(db.Float, nullable=True)
    thc_emissions_mg_per_km = db.Column(db.Float, nullable=True)
    emissions_nox_mg_per_km = db.Column(db.Float, nullable=True)
    thc_plus_nox_emissions_mg_per_km = db.Column(db.Float, nullable=True)
    particulates_no_mg_per_km = db.Column(db.Float, nullable=True)
    rde_nox_urban = db.Column(db.Float, nullable=True)
    rde_nox_combined = db.Column(db.Float, nullable=True)
    date_of_change = db.Column(db.Date, nullable=False)
    wiki_hashes = db.Column(ARRAY(db.CHAR(length=32)), nullable=True)
    year = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return '<sensors id {}>'.format(self.sensor_id)

    def __hash__(self):
        return hash(self.sensor_id)


class WikiCarModel(db.Model):
    __tablename__ = wiki_car_table
    logger.info('table name for sensors: {}'.format(__tablename__))
    hash_id = db.Column(db.CHAR(length=32), primary_key=True, unique=True)
    wiki_name = db.Column(db.String, nullable=False, index=True)
    category_short_eu = db.Column(db.String,
                                  db.ForeignKey('{}.category_short_eu'.format(
                                      wiki_category_table)),
                                  nullable=True, index=True)
    brand_name = db.Column(db.String, nullable=False, index=True)
    car_name = db.Column(db.String, nullable=False, index=True)
    page_id = db.Column(db.Integer, nullable=True)
    page_language = db.Column(db.String, nullable=True)

    def __repr__(self):
        return '<car wiki name {}>'.format(self.wiki_name)

    def __hash__(self):
        return hash(self.wiki_name)


class CarCategoryModel(db.Model):
    __tablename__ = wiki_category_table
    logger.info('table name for sensors: {}'.format(__tablename__))
    category_short_eu = db.Column(db.String, primary_key=True, unique=True, nullable=False, index=True)
    category_name_de = db.Column(db.String, unique=True, nullable=False, index=True)
    category_name_en = db.Column(db.String, unique=True, nullable=False, index=True)
    car_models = db.relationship('WikiCarModel',
                                 backref='{}'.format(wiki_category_table),
                                 lazy='dynamic')
    wiki_car_page_texts = db.relationship('WikiCarPageTextModel',
                                          backref='{}'.format(wiki_category_table),
                                          lazy='dynamic')
    carfueldata_av_statistics = db.relationship('CarFuelDataAverageCategoryStatisticsModel',
                                                backref='{}'.format(
                                                    wiki_category_table),
                                                lazy='dynamic')
    average_category_statistics = db.relationship('EnvirocarAverageCategoryStatisticsModel', backref='{}'.format(
        wiki_category_table),
                                                  lazy='dynamic')

    def __repr__(self):
        return '<category wiki {}>'.format(self.category_short_eu)

    def __hash__(self):
        return hash(self.category_short_eu)


class CountryDataModel(db.Model):
    __tablename__ = countries_table
    logger.info('table name for countries: {}'.format(__tablename__))
    country_name = db.Column(db.String, unique=True, primary_key=True, index=True, nullable=False)
    country_alpha_2 = db.Column(db.String, unique=True, primary_key=True, index=True)
    country_alpha_3 = db.Column(db.String, unique=True, primary_key=True, index=True, nullable=True)
    country_numeric = db.Column(db.Integer, primary_key=True, index=True, nullable=True)
    country_currency_code = db.Column(db.String, primary_key=True, index=True, nullable=True)
    country_currency_name = db.Column(db.String, primary_key=True, index=True, nullable=True)
    geom = db.Column(Geometry(geometry_type='MULTIPOLYGON', srid=4326, spatial_index=True))
    country_prices = db.relationship('EurostatCountryPriceModel', lazy='dynamic')

    def __repr__(self):
        return '<country_code {}>'.format(self.country_name)

    def __hash__(self):
        return hash(self.country_name)


class EnvirocarPhenomenonModel(db.Model):
    __tablename__ = ec_tables['phenomenons']
    logger.info('table name for phenomenons: {}'.format(__tablename__))

    name = db.Column(db.String, unique=True, primary_key=True)
    unit = db.Column(db.String, nullable=False)
    sensors_statistics = db.relationship('EnvirocarSensorStatisticModel', backref='{}'.format(ec_tables['phenomenons']),
                                         lazy='dynamic')
    tracks_measurements = db.relationship('EnvirocarTrackMeasurementModel',
                                          backref='{}'.format(ec_tables['phenomenons']),
                                          lazy='dynamic')
    tracks_statistics = db.relationship('EnvirocarTrackStatisticModel', backref='{}'.format(ec_tables['phenomenons']),
                                        lazy='dynamic')
    average_vehicle_type_statistics = db.relationship('EnvirocarAverageVehicleTypeStatisticModel',
                                                      backref='{}'.format(ec_tables['phenomenons']),
                                                      lazy='dynamic')
    average_manufacturer_statistics = db.relationship('EnvirocarAverageManufacturerStatisticModel',
                                                      backref='{}'.format(ec_tables['phenomenons']),
                                                      lazy='dynamic')
    average_category_statistics = db.relationship('EnvirocarAverageCategoryStatisticsModel',
                                                  backref='{}'.format(ec_tables['phenomenons']),
                                                  lazy='dynamic')

    def __repr__(self):
        return '<phenomenon name {}>'.format(self.name)

    def __hash__(self):
        return hash(self.name)


class EnvirocarSensorModel(db.Model):
    __tablename__ = ec_tables['sensors']
    logger.info('table name for sensors: {}'.format(__tablename__))
    sensor_id = db.Column(db.String, unique=True, primary_key=True, index=True)
    sensor_type = db.Column(db.String, nullable=False)
    car_model = db.Column(db.String, nullable=False)
    car_manufacturer = db.Column(db.String, nullable=False)
    fuel_type = db.Column(db.String, nullable=False)
    construction_year = db.Column(db.Integer, nullable=False)
    wiki_hashes = db.Column(ARRAY(db.CHAR(length=32)), nullable=True)
    track_ids = db.relationship('EnvirocarTrackModel', backref='{}'.format(ec_tables['sensors']), lazy='dynamic')
    sensors_statistics = db.relationship('EnvirocarSensorStatisticModel', backref='{}'.format(ec_tables['sensors']),
                                         lazy='dynamic')
    tracks_measurements = db.relationship('EnvirocarTrackMeasurementModel', backref='{}'.format(ec_tables['sensors']),
                                          lazy='dynamic')
    tracks_features = db.relationship('EnvirocarTrackFeatureModel', backref='{}'.format(ec_tables['sensors']),
                                      lazy='dynamic')

    def __repr__(self):
        return '<sensors id {}>'.format(self.sensor_id)

    def __hash__(self):
        return hash(self.sensor_id)


# TODO Always add the new agencies here to reference the correct cars
class MatchedWikiEnvirocarModel(db.Model):
    __tablename__ = misc_tables['wikipedia_envirocar_match_table']
    logger.info('table name for matched wikicar envirocar: {}'.format(__tablename__))
    object_hash = db.Column(db.CHAR(length=32), primary_key=True, unique=True)
    envirocar_sensor_id = db.Column(db.String, nullable=True, index=True)
    car_hash_id = db.Column(db.CHAR(length=32), nullable=False, index=True)


class EnvirocarSensorStatisticModel(db.Model):
    __tablename__ = ec_tables['sensors_statistics']
    logger.info('table name for sensor statistics: {}'.format(__tablename__))
    hash_id = db.Column(db.CHAR(length=32), primary_key=True, unique=True)
    sensor_id = db.Column(db.String, db.ForeignKey('{}.sensor_id'.format(ec_tables['sensors'])), nullable=False,
                          index=True)
    phenomenon_name = db.Column(db.String, db.ForeignKey('{}.name'.format(ec_tables['phenomenons'])), nullable=False,
                                index=True)
    max = db.Column(db.Float(asdecimal=True), nullable=True)
    avg = db.Column(db.Float(asdecimal=True), nullable=True)
    min = db.Column(db.Float(asdecimal=True), nullable=True)
    # Now some statistics --> numb = number of  … used for the statistics
    numb_measurements = db.Column(db.Integer, nullable=True)
    numb_tracks = db.Column(db.Integer, nullable=True)
    numb_users = db.Column(db.Integer, nullable=True)
    numb_sensors = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return '<sensor statistics with id {}>'.format(self.sensor_id)

    def __hash__(self):
        return hash(self.sensor_id)


class EnvirocarTrackModel(db.Model):
    __tablename__ = ec_tables['tracks']
    logger.info('table name for tracks: {}'.format(__tablename__))

    track_id = db.Column(db.String, unique=True, primary_key=True, index=True)
    sensor_id = db.Column(db.String, db.ForeignKey('{}.sensor_id'.format(ec_tables['sensors'])), nullable=False,
                          index=True)
    track_length = db.Column(db.Float(asdecimal=True))
    geom = db.Column(Geometry(geometry_type='LINESTRING', srid=4326, spatial_index=True), nullable=True)
    tracks_statistics = db.relationship('EnvirocarTrackStatisticModel', backref='{}'.format(ec_tables['tracks']),
                                        lazy='dynamic')
    tracks_measurements = db.relationship('EnvirocarTrackMeasurementModel', backref='{}'.format(ec_tables['tracks']),
                                          lazy='dynamic')
    tracks_features = db.relationship('EnvirocarTrackFeatureModel', backref='{}'.format(ec_tables['tracks']),
                                      lazy='dynamic')

    def __repr__(self):
        return '<track {}>'.format(self.track_id)

    def __hash__(self):
        return hash(self.track_id)


class EnvirocarTrackStatisticModel(db.Model):
    __tablename__ = ec_tables['tracks_statistics']
    logger.info('table name for track statistics: {}'.format(__tablename__))
    hash_id = db.Column(db.CHAR(length=32), primary_key=True, unique=True)
    track_id = db.Column(db.String, db.ForeignKey('{}.track_id'.format(ec_tables['tracks'])), nullable=False,
                         index=True)
    phenomenon_name = db.Column(db.String, db.ForeignKey('{}.name'.format(ec_tables['phenomenons'])), nullable=False,
                                index=True)
    max = db.Column(db.Float(asdecimal=True), nullable=True)
    avg = db.Column(db.Float(asdecimal=True), nullable=True)
    min = db.Column(db.Float(asdecimal=True), nullable=True)
    # Now some statistics --> numb = number of  … used for the statistics
    numb_measurements = db.Column(db.Integer, nullable=True)
    numb_tracks = db.Column(db.Float(asdecimal=True), nullable=True)
    numb_users = db.Column(db.Float(asdecimal=True), nullable=True)
    numb_sensors = db.Column(db.Float(asdecimal=True), nullable=True)

    def __repr__(self):
        return '<track statistics with id {}>'.format(self.track_id)

    def __hash__(self):
        return hash(self.track_id)


class EnvirocarTrackFeatureModel(db.Model):
    __tablename__ = ec_tables['tracks_features']
    logger.info('table name for track geometries: {}'.format(__tablename__))
    track_measurement_id = db.Column(db.String, index=True, unique=True, nullable=False, primary_key=True)

    sensor_id = db.Column(db.String, db.ForeignKey('{}.sensor_id'.format(ec_tables['sensors'])), nullable=False,
                          index=True)
    track_id = db.Column(db.String, db.ForeignKey('{}.track_id'.format(ec_tables['tracks'])), nullable=False,
                         index=True)

    geom = db.Column(Geometry(geometry_type='POINT', srid=4326, spatial_index=True))

    tracks_features = db.relationship('EnvirocarTrackMeasurementModel',
                                      backref='{}'.format(ec_tables['tracks_features']),
                                      lazy='dynamic')

    def __repr__(self):
        return '<track geometries with id {}>'.format(self.country_name)

    def __hash__(self):
        return hash(self.country_name)


class EnvirocarTrackMeasurementModel(db.Model):
    __tablename__ = ec_tables['tracks_measurements']
    logger.info('table name for track measurements: {}'.format(__tablename__))

    hash_id = db.Column(db.CHAR(length=32), primary_key=True, unique=True)
    track_measurement_id = db.Column(db.String,
                                     db.ForeignKey('{}.track_measurement_id'.format(ec_tables['tracks_features'])),
                                     nullable=False, index=True)

    track_id = db.Column(db.String, db.ForeignKey('{}.track_id'.format(ec_tables['tracks'])), nullable=False,
                         index=True)
    sensor_id = db.Column(db.String, db.ForeignKey('{}.sensor_id'.format(ec_tables['sensors'])), nullable=False,
                          index=True)
    phenomenon_name = db.Column(db.String, db.ForeignKey('{}.name'.format(ec_tables['phenomenons'])), nullable=False,
                                index=True)
    phenomenon_value = db.Column(db.Float(asdecimal=True), nullable=True)
    date = db.Column(db.DateTime, nullable=False, index=True)

    def __repr__(self):
        return '<track measurements with id {}>'.format(self.track_id)

    def __hash__(self):
        return hash(self.track_id)


class CarFuelDataAverageCategoryStatisticsModel(db.Model):
    __tablename__ = misc_tables['cfd_average_category_statistics']
    hash_id = db.Column(db.CHAR(length=32), primary_key=True, unique=True)
    vehicle_type = db.Column(db.String, nullable=False, index=True)
    fuel_type = db.Column(db.String, nullable=False, index=True)
    phenomenon_name = db.Column(db.String, nullable=False, index=True)
    value = db.Column(db.Float, nullable=False)
    numb_cars = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False, index=True)
    category_short_eu = db.Column(db.String, db.ForeignKey(
        '{}.category_short_eu'.format(wiki_category_table)))


class EnvirocarAverageCategoryStatisticsModel(db.Model):
    __tablename__ = misc_tables['ec_average_category_statistics']
    hash_id = db.Column(db.CHAR(length=32), primary_key=True, unique=True)
    vehicle_type = db.Column(db.String, nullable=False, index=True)
    fuel_type = db.Column(db.String, nullable=False, index=True)
    phenomenon_name = db.Column(db.String, db.ForeignKey('{}.name'.format(ec_tables['phenomenons'])), nullable=False,
                                index=True)
    max = db.Column(db.Float(asdecimal=True))
    average = db.Column(db.Float(asdecimal=True))
    min = db.Column(db.Float(asdecimal=True))
    measurements = db.Column(db.Integer, nullable=False)
    numb_sensors = db.Column(db.Integer, nullable=False)
    category_short_eu = db.Column(db.String, db.ForeignKey(
        '{}.category_short_eu'.format(wiki_category_table)))


class EnvirocarAverageVehicleTypeStatisticModel(db.Model):
    __tablename__ = ec_tables['average_vehicle_type_statistics']
    hash_id = db.Column(db.CHAR(length=32), primary_key=True, unique=True)
    vehicle_type = db.Column(db.String, nullable=False, index=True)
    fuel_type = db.Column(db.String, nullable=False, index=True)
    phenomenon_name = db.Column(db.String, db.ForeignKey('{}.name'.format(ec_tables['phenomenons'])), nullable=False,
                                index=True)
    max = db.Column(db.Float(asdecimal=True))
    average = db.Column(db.Float(asdecimal=True))
    min = db.Column(db.Float(asdecimal=True))
    measurements = db.Column(db.Integer, nullable=False)
    numb_sensors = db.Column(db.Integer, nullable=False)


class EnvirocarAverageManufacturerStatisticModel(db.Model):
    __tablename__ = ec_tables['average_manufacturer_statistics']
    hash_id = db.Column(db.CHAR(length=32), primary_key=True, unique=True)
    manufacturer = db.Column(db.String, nullable=False, index=True)
    vehicle_type = db.Column(db.String, nullable=False, index=True)
    fuel_type = db.Column(db.String, nullable=False, index=True)
    phenomenon_name = db.Column(db.String, db.ForeignKey('{}.name'.format(ec_tables['phenomenons'])), nullable=False,
                                index=True)
    max = db.Column(db.Float(asdecimal=True))
    average = db.Column(db.Float(asdecimal=True))
    min = db.Column(db.Float(asdecimal=True))
    measurements = db.Column(db.Integer, nullable=False)
    numb_sensors = db.Column(db.Integer, nullable=False)


class EurostatCountryPriceModel(db.Model):
    __tablename__ = es_tables['country_prices']
    hash_id = db.Column(db.CHAR(length=32), primary_key=True, unique=True)
    date = db.Column(db.DateTime, nullable=False, index=True)
    country_alpha_2 = db.Column(db.String,
                                db.ForeignKey('{}.country_alpha_2'.format(countries_table)),
                                nullable=False, index=True)
    taux = db.Column(db.Float)
    euro_price = db.Column(db.Integer, nullable=True)
    euro_ht = db.Column(db.Numeric, nullable=True)
    euro_ttc = db.Column(db.Numeric, nullable=True)
    euro_unit = db.Column(db.String, nullable=False)
    euro_quantity = db.Column(db.Integer, nullable=False)
    diesel_ht = db.Column(db.Numeric, nullable=True)
    diesel_ttc = db.Column(db.Numeric, nullable=True)
    diesel_unit = db.Column(db.String, nullable=False)
    diesel_quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<CountryPrice date {}>'.format(self.date)

    def __hash__(self):
        return hash(self.date)


# TODO think about clustering general prices into geographical regions?! e.g. (West-) Europe, Asia etc.
class EurostatGeneralPriceModel(db.Model):
    __tablename__ = es_tables['general_prices']
    hash_id = db.Column(db.CHAR(length=32), primary_key=True, unique=True)
    date = db.Column(db.DateTime, nullable=False, primary_key=True, unique=True)
    euro_price = db.Column(db.Integer, nullable=True)
    euro_ht = db.Column(db.Numeric, nullable=True)
    euro_ttc = db.Column(db.Numeric, nullable=True)
    euro_unit = db.Column(db.String, nullable=False)
    euro_quantity = db.Column(db.Integer, nullable=False)
    diesel_ht = db.Column(db.Numeric, nullable=True)
    diesel_ttc = db.Column(db.Numeric, nullable=True)
    diesel_unit = db.Column(db.String, nullable=False)
    diesel_quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<general price date {}>'.format(self.date)

    def __hash__(self):
        return hash(self.date)


class HashModel(db.Model):
    __tablename__ = hash_table
    uuid = db.Column(db.Binary(length=16), nullable=False, primary_key=True, unique=True)
    object_name = db.Column(db.String, nullable=False, primary_key=True)
    object_hash = db.Column(db.String, nullable=False, primary_key=True, unique=True)
    hash_date = db.Column(db.Date, nullable=False, primary_key=False, unique=False)

    def __repr__(self):
        return '<Hash Table object {}>'.format(self.object_name)

    def __hash__(self):
        return hash(self.object_name)
