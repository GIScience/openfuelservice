import hashlib

from sqlalchemy.exc import IntegrityError
from tqdm import tqdm

from openfuelservice.server import db
from openfuelservice.server.db_import.envirocar.objects import PhenomenonObject, TrackObject, SensorObject, \
    SensorStatisticObject, TrackMeasurementObject, TrackFeatureObject
from openfuelservice.server.db_import.models import EnvirocarPhenomenonModel, EnvirocarTrackModel, EnvirocarSensorModel, \
    EnvirocarSensorStatisticModel, EnvirocarTrackStatisticModel, \
    EnvirocarTrackMeasurementModel, EnvirocarTrackFeatureModel, EnvirocarAverageVehicleTypeStatisticModel, \
    EnvirocarAverageManufacturerStatisticModel
from openfuelservice.server.statistics.objects import AverageEnviroCarVehicleTypeStatisticObject, \
    AverageEnviroCarManufacturerStatisticObject
from openfuelservice.server.utils.misc.mappings import DataMappings


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
                    db.session.merge(collection_object)
                    db.session.commit()
                except Exception as err:
                    print(err)
                    db.session.rollback()
        else:
            print(err)


def fallback_importer_return(object_collection: [], return_collection: []) -> []:
    """
    Working as the general importer with a fallback strategy build in. If an object exists error is raised by a
    collection, a unique import strategy is used. If another error occurs, it is printed.

    :param return_collection: Collection to add successful committed objects to
    :param object_collection: collection of Database Models
    """
    try:
        db.session.add_all(object_collection)
        db.session.commit()
        for element in object_collection:
            return_collection.append(element)
        return return_collection
    except Exception as err:
        db.session.rollback()
        if type(err) == IntegrityError:
            for collection_object in object_collection:
                try:
                    db.session.add(collection_object)
                    db.session.commit()
                    return_collection.append(collection_object)
                except Exception as err:
                    db.session.rollback()
            return return_collection
        else:
            print(err)


class EnvirocarImporter:
    def __init__(self):
        # Temp variable to verify the data
        self.ec_av_vehicle_type_statistics = []
        self.ec_av_manufacturer_statistics = []
        self.new_data = dict()
        self.ec_phenomenons = []
        self.ec_tracks = []
        self.ec_sensors = []
        self.ec_sensor_statistics = []
        self.ec_tracks = []
        self.ec_tracks_new = []
        self.ec_tracks_statistics = []
        self.ec_tracks_measurements = []
        self.ec_tracks_features = []
        self.ec_object = []

    def create_phenomenon(self, phenomenon: dict):
        name = phenomenon['name']
        unit = phenomenon['unit']
        self.store_phenomenon(PhenomenonObject(
            name=name,
            unit=unit
        ))

    def store_phenomenon(self, phenomenon_object: PhenomenonObject):
        self.ec_phenomenons.append(EnvirocarPhenomenonModel(
            name=phenomenon_object.name,
            unit=phenomenon_object.unit
        ))
        # Phenomenons too small for in between push!

    def create_sensor(self, sensor: dict):
        sensor_id = sensor['sensor_id']
        sensor_type = sensor['type']
        car_model = sensor['model']
        fuel_type = sensor['fuel_type']
        real_fuel_type = DataMappings().get_fuel_type(fuel_type_to_check=fuel_type)
        construction_year = sensor['construction_year']
        car_manufacturer = sensor['manufacturer']
        wiki_hashes = []
        self.store_sensor(SensorObject(
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            car_model=car_model,
            car_manufacturer=car_manufacturer,
            fuel_type=real_fuel_type if real_fuel_type is not False else fuel_type,
            construction_year=construction_year,
            wiki_hashes=[]
        ))

    def store_sensor(self, sensor: SensorObject):
        fuel_type = sensor.fuel_type
        real_fuel_type = DataMappings().get_fuel_type(fuel_type_to_check=fuel_type)
        self.ec_sensors.append(EnvirocarSensorModel(
            sensor_id=sensor.sensor_id,
            sensor_type=sensor.sensor_type,
            car_model=sensor.car_model,
            fuel_type=real_fuel_type if real_fuel_type is not False else fuel_type,
            construction_year=sensor.construction_year,
            car_manufacturer=sensor.car_manufacturer,
            wiki_hashes=sensor.wiki_hashes
        ))

    def create_sensor_statistic(self, sensor_id: str, sensor_statistics: dict):
        # Check if the sensor statistics element contains any values
        if len(sensor_statistics) > 0:
            for phenomenon in sensor_statistics:
                max = sensor_statistics[phenomenon]['max'][0]
                avg = sensor_statistics[phenomenon]['avg'][0]
                min = sensor_statistics[phenomenon]['min'][0]
                numb_measurements = sensor_statistics[phenomenon]['measurements'][0]
                numb_tracks = sensor_statistics[phenomenon]['tracks'][0]
                numb_users = sensor_statistics[phenomenon]['users'][0]
                numb_sensors = sensor_statistics[phenomenon]['sensors'][0]
                self.store_sensor_statistic(SensorStatisticObject(
                    sensor_id=sensor_id,
                    phenomenon_name=phenomenon,
                    max=max,
                    avg=avg,
                    min=min if float(min) > 0 else 0,
                    numb_measurements=numb_measurements,
                    numb_tracks=numb_tracks,
                    numb_users=numb_users,
                    numb_sensors=numb_sensors
                ))
        pass

    def store_sensor_statistic(self, sensor_statistic_object: SensorStatisticObject):
        self.ec_sensor_statistics.append(EnvirocarSensorStatisticModel(
            hash_id=hashlib.md5((str(sensor_statistic_object.sensor_id).strip() +
                                 str(sensor_statistic_object.phenomenon_name).strip()
                                 ).encode(encoding='UTF-8', errors='ignore')).hexdigest(),
            sensor_id=sensor_statistic_object.sensor_id,
            phenomenon_name=sensor_statistic_object.phenomenon_name,
            max=sensor_statistic_object.max,
            avg=sensor_statistic_object.avg,
            min=sensor_statistic_object.min,
            numb_measurements=sensor_statistic_object.numb_measurements,
            numb_tracks=sensor_statistic_object.numb_tracks,
            numb_users=sensor_statistic_object.numb_users,
            numb_sensors=sensor_statistic_object.numb_sensors
        ))

    def create_track(self, track: dict):
        track_id = track['track_id']
        sensor_id = track['sensor_id']
        track_length = track['track_length']
        self.store_track(TrackObject(
            track_id=track_id,
            sensor_id=sensor_id,
            track_length=track_length
        ))

    def store_track(self, track_object: TrackObject):
        self.ec_tracks.append(EnvirocarTrackModel(
            track_id=track_object.track_id,
            sensor_id=track_object.sensor_id,
            track_length=track_object.track_length
        ))
        if len(self.ec_tracks) > 5000:
            self.ec_tracks_new = fallback_importer_return(self.ec_tracks, self.ec_tracks_new)
            self.ec_tracks = []

    def store_track_statistic(self, track_statistic_object: EnvirocarTrackStatisticModel):
        self.ec_tracks_statistics.append(EnvirocarTrackStatisticModel(
            hash_id=hashlib.md5(
                (str(track_statistic_object.track_id).strip() + str(
                    track_statistic_object.phenomenon_name).strip()).encode(encoding='UTF-8',
                                                                            errors='ignore')).hexdigest(),
            track_id=track_statistic_object.track_id,
            phenomenon_name=track_statistic_object.phenomenon_name,
            max=track_statistic_object.avg,
            min=track_statistic_object.min,
            numb_measurements=track_statistic_object.numb_measurements,
            numb_tracks=track_statistic_object.numb_tracks,
            numb_users=track_statistic_object.numb_users,
            numb_sensors=track_statistic_object.numb_sensors
        ))
        if len(self.ec_tracks_statistics) > 100000:
            fallback_importer(self.ec_tracks_statistics)
            self.ec_tracks_statistics = []

    def store_track_measurement(self, measurement: TrackMeasurementObject):
        self.ec_tracks_measurements.append(EnvirocarTrackMeasurementModel(
            hash_id=hashlib.md5(
                (str(measurement.track_measurement_id).strip() + str(measurement.phenomenon_name).strip()).encode(
                    encoding='UTF-8', errors='ignore')).hexdigest(),
            track_measurement_id=measurement.track_measurement_id,
            track_id=measurement.track_id,
            sensor_id=measurement.sensor_id,
            phenomenon_name=measurement.phenomenon_name,
            phenomenon_value=measurement.phenomenon_value,
            date=measurement.date
        ))
        if len(self.ec_tracks_measurements) > 100000:
            fallback_importer(self.ec_tracks_measurements)
            self.ec_tracks_measurements = []

    def store_track_feature(self, feature: TrackFeatureObject):
        self.ec_tracks_features.append(EnvirocarTrackFeatureModel(
            track_measurement_id=feature.track_measurement_id,
            sensor_id=feature.sensor_id,
            track_id=feature.track_id,
            geom=feature.geom
        ))
        if len(self.ec_tracks_features) > 100000:
            fallback_importer(self.ec_tracks_features)
            self.ec_tracks_features = []

    def store_average_vehicle_type_statistics(self, statistic: AverageEnviroCarVehicleTypeStatisticObject):
        fuel_type = statistic.fuel_type
        real_fuel_type = DataMappings().get_fuel_type(fuel_type_to_check=fuel_type)

        self.ec_av_vehicle_type_statistics.append(EnvirocarAverageVehicleTypeStatisticModel(
            hash_id=hashlib.md5(
                (str(statistic.vehicle_type).strip() + str(statistic.fuel_type).strip() + str(
                    statistic.phenomenon).strip()).encode(encoding='UTF-8', errors='ignore')).hexdigest(),
            vehicle_type=statistic.vehicle_type,
            fuel_type=real_fuel_type if not False else fuel_type,
            phenomenon_name=statistic.phenomenon,
            max=statistic.max,
            average=statistic.average,
            min=statistic.min,
            measurements=statistic.measurements,
            numb_sensors=statistic.numb_sensors
        ))

    def store_average_manufacturer_statistics(self, statistic: AverageEnviroCarManufacturerStatisticObject):
        fuel_type = statistic.fuel_type
        real_fuel_type = DataMappings().get_fuel_type(fuel_type_to_check=fuel_type)
        self.ec_av_manufacturer_statistics.append(EnvirocarAverageManufacturerStatisticModel(
            hash_id=hashlib.md5(
                (str(statistic.manufacturer).strip() + str(statistic.fuel_type).strip() + str(
                    statistic.phenomenon).strip()).encode(encoding='UTF-8', errors='ignore')).hexdigest(),
            manufacturer=statistic.manufacturer,
            vehicle_type=statistic.vehicle_type,
            fuel_type=real_fuel_type if real_fuel_type is not False else fuel_type,
            phenomenon_name=statistic.phenomenon,
            max=statistic.max,
            average=statistic.average,
            min=statistic.min,
            measurements=statistic.measurements,
            numb_sensors=statistic.numb_sensors
        ))

    def import_phenomenons(self, phenomenons: dict):
        for phenomenon in tqdm(phenomenons, total=len(phenomenons), unit=' Importing Envirocar Phenomenons'):
            self.create_phenomenon(phenomenons[phenomenon])
        fallback_importer(self.ec_phenomenons)

    def import_tracks(self, tracks: dict):
        for track in tqdm(tracks, total=len(tracks), unit=' Importing Envirocar Tracks'):
            self.create_track(tracks[track])
        fallback_importer(self.ec_tracks)

    def import_sensors(self, sensors):
        for sensor in tqdm(sensors, total=len(sensors), unit=' Importing Envirocar Sensors'):
            if type(sensor) == EnvirocarSensorModel:
                self.ec_sensors.append(sensor)
            elif type(sensor) == str:
                try:
                    self.create_sensor(sensors[sensor])
                except TypeError as err:
                    print(err)
                    pass
        fallback_importer(self.ec_sensors)

    def import_sensors_statistics(self, sensors_statistics: dict):
        for sensor_id in tqdm(sensors_statistics, total=len(sensors_statistics),
                              unit=' Importing Envirocar Sensors Statistics'):
            self.create_sensor_statistic(sensor_id=sensor_id, sensor_statistics=sensors_statistics[sensor_id])
        fallback_importer(self.ec_sensor_statistics)

    def import_tracks_measurements(self, measurements: list):
        for measurement in tqdm(measurements, total=len(measurements), unit=' Importing Envirocar Track Measurements'):
            self.store_track_measurement(measurement)
        fallback_importer(self.ec_tracks_measurements)

    def import_tracks_features(self, features: list):
        for feature in tqdm(features, total=len(features), unit=' Importing Envirocar Track Features'):
            self.store_track_feature(feature)
        fallback_importer(self.ec_tracks_features)

    def import_tracks_statistics(self, tracks_statistics: list):
        for statistic in tqdm(tracks_statistics, total=len(tracks_statistics),
                              unit=' Importing Envirocar Tracks Statistics'):
            self.store_track_statistic(statistic)
        fallback_importer(self.ec_tracks_statistics)

    def import_average_vehicle_type_statistics(self, statistics: list):
        for statistic in tqdm(statistics, total=len(statistics),
                              unit=' Importing Envirocar Average Vehicle Statistics'):
            self.store_average_vehicle_type_statistics(statistic)
        fallback_importer(self.ec_av_vehicle_type_statistics)

    def import_average_manufacturer_statistics(self, statistics: list):
        for statistic in tqdm(statistics, total=len(statistics),
                              unit=' Importing Envirocar Average Manufacturer Statistics'):
            self.store_average_manufacturer_statistics(statistic)
        fallback_importer(self.ec_av_manufacturer_statistics)
