import hashlib

from sqlalchemy.exc import IntegrityError
from tqdm import tqdm

from openfuelservice.server import db
from openfuelservice.server.db_import.models import MatchedWikiEnvirocarModel, EnvirocarAverageCategoryStatisticsModel, \
    CarFuelDataAverageCategoryStatisticsModel
from openfuelservice.server.statistics.objects import AverageEnviroCarCategoryStatisticObject, \
    AverageCFDCategoryStatisticObject


def fallback_importer(object_collection: []):
    """
    Working as the general importer with a fallback strategy build in. If an object exists error is raised by a
    collection, a unique import strategy is used. If another error occurs, it is printed.
    It is not capable of updating data that only got an increment unique id as a primary key!a

    :param object_collection: collection of Database Models
    """
    try:
        db.session.bulk_save_objects(object_collection, update_changed_only=True)
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        if type(err) == IntegrityError:
            for collection_object in object_collection:
                try:
                    db.session.add(collection_object)
                    db.session.commit()
                except Exception as err:
                    db.session.rollback()
        else:
            print(err)


class MatchedImporter:
    def __init__(self):
        self.matched_objects = []

    def import_matched_wikicar_envirocar(self, matched_objects):
        for matched_object in tqdm(matched_objects, total=len(matched_objects),
                                   unit=' Importing Matched Wikicar Envirocar Objects'):
            self.store_matched_wikicar_envirocar_objects(matched_object=matched_object)
        fallback_importer(self.matched_objects)
        self.matched_objects = []

    def store_matched_wikicar_envirocar_objects(self, matched_object):
        sensor_id = matched_object.sensor_id
        car_hash_id = matched_object.car_hash_id
        category_short_eu = matched_object.category_short_eu
        self.matched_objects.append(MatchedWikiEnvirocarModel(
            object_hash=hashlib.md5((str(category_short_eu).strip() +
                                     str().strip(sensor_id) +
                                     str(car_hash_id).strip()).encode(encoding='UTF-8', errors='ignore')).hexdigest(),
            envirocar_sensor_id=sensor_id,
            car_hash_id=car_hash_id
        ))


class MiscImporter:
    def __init__(self):
        self.av_category_statistics = []

    def store_av_ec_category_statistics(self, av_category_statistic: AverageEnviroCarCategoryStatisticObject):
        vehicle_type = av_category_statistic.vehicle_type,
        fuel_type = av_category_statistic.fuel_type,
        phenomenon_name = av_category_statistic.phenomenon,
        category_short_eu = av_category_statistic.category_short_eu,
        self.av_category_statistics.append(EnvirocarAverageCategoryStatisticsModel(
            # TODO Add hash id
            hash_id=hashlib.md5((str(vehicle_type).strip() +
                                 str(fuel_type).strip() +
                                 str(phenomenon_name).strip() +
                                 str(category_short_eu).strip()).encode(encoding='UTF-8', errors='ignore')).hexdigest(),
            vehicle_type=vehicle_type,
            fuel_type=fuel_type,
            phenomenon_name=phenomenon_name,
            category_short_eu=category_short_eu,
            max=av_category_statistic.max,
            average=av_category_statistic.average,
            min=av_category_statistic.min,
            measurements=av_category_statistic.measurements,
            numb_sensors=av_category_statistic.numb_sensors
        ))

    def store_av_cfd_category_statistics(self, av_category_statistic: AverageCFDCategoryStatisticObject):
        vehicle_type = av_category_statistic.vehicle_type,
        fuel_type = av_category_statistic.fuel_type,
        phenomenon_name = av_category_statistic.phenomenon,
        category_short_eu = av_category_statistic.category_short_eu,
        year = av_category_statistic.year
        self.av_category_statistics.append(CarFuelDataAverageCategoryStatisticsModel(
            # TODO Add hash id
            hash_id=hashlib.md5((str(vehicle_type).strip() +
                                 str(fuel_type).strip() +
                                 str(phenomenon_name).strip() +
                                 str(year) +
                                 str(category_short_eu).strip()).encode(encoding='UTF-8', errors='ignore')).hexdigest(),
            vehicle_type=vehicle_type,
            fuel_type=fuel_type,
            phenomenon_name=phenomenon_name,
            category_short_eu=category_short_eu,
            value=av_category_statistic.value,
            numb_cars=av_category_statistic.numb_cars,
            year=year
        ))

    def import_average_ec_category_stats(self, av_category_statistics):
        av_category_statistic: AverageEnviroCarCategoryStatisticObject
        for av_category_statistic in tqdm(av_category_statistics, unit=' Importing EnviroCar Average Data',
                                          total=len(av_category_statistics)):
            self.store_av_ec_category_statistics(av_category_statistic=av_category_statistic)
        fallback_importer(self.av_category_statistics)
        self.av_category_statistics = []

    def import_average_cfd_category_stats(self, av_category_statistics):
        av_category_statistic: AverageCFDCategoryStatisticObject
        for av_category_statistic in tqdm(av_category_statistics, unit=' Importing CarFuelData Average Data',
                                          total=len(av_category_statistics)):
            self.store_av_cfd_category_statistics(av_category_statistic=av_category_statistic)
        fallback_importer(self.av_category_statistics)
        self.av_category_statistics = []
