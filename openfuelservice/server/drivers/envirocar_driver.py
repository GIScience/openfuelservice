import time
from multiprocessing.dummy import Pool as ThreadPool

import requests
from geoalchemy2 import shape as geo_shape
from shapely.geometry import shape
from tqdm import tqdm

from openfuelservice.server import ofs_settings, car_brands, verbose
from openfuelservice.server.db_import.envirocar.objects import TrackMeasurementObject, TrackFeatureObject, \
    TrackStatisticObject
from openfuelservice.server.statistics.envirocar_statistics import AverageStatistics
from openfuelservice.server.utils.misc import file_management
from openfuelservice.server.utils.misc.file_management import get_response

manufacturer_aliases = car_brands['aliases']
manufacturers = car_brands['brands']
enviro_settings = ofs_settings['statistics_provider']['envirocar_provider']
crawl_test = enviro_settings['crawl_test']
crawl_amount = enviro_settings['crawl_amount']
url = enviro_settings['api_url']
cpu = ofs_settings['general']['cpu']
counter = 0
querystring = {"limit": "100"}
headers = {
    # empty for now
}


def check_manufacturer(manufacturer_to_check: str) -> str:
    cleaned_manufacturer_to_check = manufacturer_to_check.casefold().strip()
    for manufacturer in manufacturer_aliases:
        if cleaned_manufacturer_to_check == manufacturer.casefold().strip():
            return manufacturer
        elif cleaned_manufacturer_to_check in manufacturer_aliases[manufacturer]:
            return manufacturer
    for manufacturer in car_brands['brands']:
        if manufacturer_to_check == manufacturer:
            return manufacturer
        if cleaned_manufacturer_to_check == manufacturer.casefold().strip():
            return manufacturer
    return ""


class Merge:
    @staticmethod
    def sensors_and_statistics(sensors, sensor_statistics):
        counter = 0
        missing_counter = 0
        for sensor in sensors:
            if sensor in sensor_statistics and len(sensor_statistics[sensor]) > 0:
                sensors[sensor]['statistics'] = sensor_statistics[sensor]
                counter += 1
            else:
                missing_counter += 1
        print("{} Sensors and Statistics matched | {} Sensor-Statistics missing".format(counter, missing_counter))
        return sensors

    @staticmethod
    def sensors_and_tracks(sensors, tracks):
        counter_1 = 0
        valid_tracks = dict()
        for track in tracks:
            track_sensor = tracks[track]['sensor_id']
            if track_sensor in sensors:
                valid_tracks[track_sensor] = track_sensor
                if 'track_ids' in sensors[track_sensor]:
                    track_length = tracks[track]['track_length']
                    track_id = tracks[track]['track_id']
                    temp_track = dict()
                    temp_track['track_length'] = track_length
                    temp_track['track_id'] = track_id
                    sensor_length = sensors[track_sensor]['total_tracks_length']
                    sensors[track_sensor]['total_tracks_length'] = sensor_length + track_length
                    sensors[track_sensor]['track_ids'][track] = temp_track
                else:
                    counter_1 += 1
                    temp_track = dict()
                    track_length = tracks[track]['track_length']
                    temp_track['track_length'] = track_length
                    track_id = tracks[track]['track_id']
                    temp_track['track_id'] = track_id
                    sensors[track_sensor]['total_tracks_length'] = track_length
                    sensors[track_sensor]['track_ids'] = dict()
                    sensors[track_sensor]['track_ids'][track] = temp_track
        print("{} Sensors with multiple Tracks | {} Sensors with single Tracks".format(len(sensors) - counter_1,
                                                                                       counter_1 - (len(
                                                                                           sensors) - counter_1)))
        return sensors


class Repair:

    @staticmethod
    def repair_tracks(sensors, tracks):
        print("Checking and repairing tracks")
        missing_sensor = 0
        track_counter = 0
        for track in tqdm(tracks, total=len(tracks), unit=' Repairing Envirocar Tracks'):
            track_sensor = tracks[track]['sensor_id']
            if track_sensor not in sensors:
                sensor = file_management.get_response(url=url + '/sensors/' + track_sensor).json()
                real_sensor_id = sensor['properties']['id']
                tracks[track]['sensor_id'] = real_sensor_id
                missing_sensor += 1  #
            track_counter += 1
        print("Successfully repaired {} of {} Tracks".format(missing_sensor, track_counter))
        return tracks


class Phenomenons:
    def get(self):
        global counter
        counter = 0
        phenomenons = {}
        print("Crawl Phenomenons")
        while True:
            start_time = time.time()
            while True:
                phenomenons_url = url + '/phenomenons'
                response = requests.request("GET", phenomenons_url, headers=headers)
                content = response.json()['phenomenons']
                phenomenons.update(self.process(content))
                counter += 1
                break
            end_time = time.time()
            break
        print("Crawl-Result: {} Phenomenons | {} Seconds".format(phenomenons.__len__(), end_time - start_time))

        return phenomenons

    @staticmethod
    def process(content):
        phenomenons = {}
        for element in content:
            phenomenons[element['name']] = dict(name=element['name'], unit=element['unit'])
        return phenomenons


class Tracks:
    tracks = {}

    @classmethod
    def fetch(cls, track_url):
        content = get_response(url=track_url)
        for track in content.json()['tracks']:
            cls.tracks.update(cls.process(track))

    @staticmethod
    def process(track):
        global counter
        track_return = {}
        if 'length' not in track:
            track[track['id']] = dict(track_id=track['id'], sensor_id=track['sensor']['properties']['id'],
                                      track_length=0)

            counter += 1
        else:
            track_return[track['id']] = dict(track_id=track['id'], sensor_id=track['sensor']['properties']['id'],
                                             track_length=track['length'])
            counter += 1
        return track_return

    def get(self):
        global counter
        counter = 0
        tracks_url = url + '/tracks'
        response = requests.request("GET", tracks_url, headers=headers, params=querystring, timeout=10)
        last_url = response.links.get('last')['url']
        print("Crawl Track pages")
        while True:
            start_time = time.time()
            temp_urls = []
            page = 0
            # second loop to measure time correctly
            while True:
                temp_url = tracks_url + "?limit=100&page={}".format(page)
                temp_urls.append(temp_url)
                page += 1
                if temp_url == last_url:
                    break
            with ThreadPool(cpu) as pool:
                for _ in tqdm(pool.imap_unordered(self.fetch, temp_urls), total=len(temp_urls),
                              unit=' Processing Track Pages'):
                    pass
            pool.close()
            pool.join()
            end_time = time.time()
            break
        print("Crawl-Result: {} Track pages | {} Tracks | {} Seconds".format(page, counter, end_time - start_time))
        return self.tracks


class TrackStatistics:
    tracks_statistics = []
    counter = 0

    @classmethod
    def process(cls, track_id: str, track_statistics):
        for statistic in track_statistics['statistics']:
            phenomenon = statistic['phenomenon']
            cls.tracks_statistics.append(TrackStatisticObject(
                track_id=track_id,
                phenomenon_name=phenomenon['name'],
                max=phenomenon['max'],
                avg=phenomenon['avg'],
                min=phenomenon['min'],
                numb_measurements=phenomenon['measurements'],
                numb_tracks=phenomenon['tracks'],
                numb_users=phenomenon['users'],
                numb_sensors=phenomenon['sensors']
            ))

    @classmethod
    def fetch(cls, track_id):
        if crawl_test and cls.counter >= crawl_amount:
            pass
        else:
            statistics_url = url + '/tracks/{}/statistics'.format(track_id)
            statistics = file_management.get_response(statistics_url).json()
            cls.process(track_id, statistics)
            cls.counter += 1

    def get(self, tracks):
        start_time = time.time()
        print("Crawl Track-Statistics")
        with ThreadPool(cpu) as pool:
            for _ in tqdm(pool.imap_unordered(self.fetch, tracks), total=len(tracks),
                          unit=' Processing Track statistics'):
                pass
        pool.close()
        pool.join()
        end_time = time.time()
        print("Crawl-Result: {} Track-Statistics | {} Seconds".format(self.counter, end_time - start_time))
        return self.tracks_statistics


class TrackMeasurements:
    # TODO Finish. Crawl decision --> Per track(slower, less overhead, more precise) -->
    # --> or crawl all pages and combine them with tracks(less calls)? I tend to per track. With a huge wait time!
    tracks_measurements = dict()
    tracks_measurements['features'] = []
    tracks_measurements['measurements'] = []
    counter = 0
    tracks_measurements_phenomenons = 0

    @classmethod
    def process(cls, track_measurements):
        for statistic in track_measurements['features']:
            properties = statistic['properties']
            phenomenons = properties['phenomenons']
            track_measurement_id = properties['id']
            track_id = properties['track']
            sensor_id = properties['sensor']['properties']['id']
            geom = statistic['geometry']
            cls.tracks_measurements['features'].append(TrackFeatureObject(
                track_measurement_id=track_measurement_id,
                track_id=track_id,
                sensor_id=sensor_id,
                geom=geo_shape.from_shape(shape(geom), srid=4326)
            ))
            for phenomenon in phenomenons:
                cls.tracks_measurements['measurements'].append(TrackMeasurementObject(
                    track_measurement_id=track_measurement_id,
                    track_id=track_id,
                    sensor_id=sensor_id,
                    phenomenon_name=phenomenon,
                    phenomenon_value=phenomenons[phenomenon]['value'],
                    date=properties['time']
                ))
                cls.tracks_measurements_phenomenons += 1

    @classmethod
    def fetch(cls, single_track):
        if crawl_test and cls.counter >= crawl_amount:
            pass
        else:
            statistics_url = url + '/tracks/{}/measurements'.format(single_track)
            statistics = file_management.get_linked_json_content(statistics_url)
            if len(statistics) > 0:
                cls.process(statistics)
                cls.counter += 1

    def get(self, tracks):
        start_time = time.time()
        print("Crawl EnvirocarTrackModel-Measurements")
        with ThreadPool(cpu) as pool:
            for _ in tqdm(pool.imap_unordered(self.fetch, tracks), total=len(tracks),
                          unit=' Processing EnvirocarTrackModel Measurements'):
                pass
        pool.close()
        pool.join()
        end_time = time.time()
        print("Crawl-Result: {} EnvirocarTrackModel-Measurements with {} phenomenons | {} Seconds".format(self.counter,
                                                                                                          self.tracks_measurements_phenomenons,
                                                                                                          end_time - start_time))
        return self.tracks_measurements


class Sensors(object):

    def __init__(self):
        self.sensors = {}
        self.missed_matches = list()

    def fetch(self, sensor_url):
        sensors = file_management.get_response(sensor_url).json()['sensors']
        self.sensors.update(self.process(sensors))

    def process(self, content):
        sensors = {}
        for element in content:
            if element['type'] != 'FeatureCollection':
                manufacturer = element['properties']['manufacturer'].strip()
                real_manufacturer = ""
                model = element['properties']['model'].strip().lower()
                search_string = manufacturer + ' ' + model
                if manufacturer in car_brands['vehicles'] and model is not "":
                    for vehicle in car_brands['vehicles']:
                        if manufacturer == vehicle:
                            real_manufacturer = car_brands['vehicles'][manufacturer]['brand']
                            real_model = car_brands['vehicles'][manufacturer]['name']
                            cleaned_model = model.replace(manufacturer, '').strip()
                            model = real_model + ' ' + cleaned_model
                        pass
                elif search_string in car_brands['vehicles'] or model in car_brands['vehicles']:
                    for vehicle in car_brands['vehicles']:
                        if search_string == vehicle or model == vehicle:
                            real_manufacturer = car_brands['vehicles'][search_string]['brand']
                            model = car_brands['vehicles'][search_string]['name']
                            break
                # For models that have the model and brand at once
                else:
                    real_manufacturer = check_manufacturer(manufacturer)
                    search_string = real_manufacturer + ' ' + model
                    if search_string in car_brands['vehicles']:
                        real_manufacturer = car_brands['vehicles'][search_string]['brand']
                        model = car_brands['vehicles'][search_string]['name']
                        pass
                if real_manufacturer != "" and model != "":
                    sensor_properties = dict(sensor_id=element['properties']['id'],
                                             type=element['type'],
                                             model=model,
                                             fuel_type=element['properties']['fuelType'],
                                             construction_year=element['properties']['constructionYear'],
                                             manufacturer=real_manufacturer)
                    sensors[element['properties']['id']] = sensor_properties
                else:
                    if verbose:
                        print("Envirocar Object not in List: Manufacturer: {} | Car: {}".format(manufacturer, model))
        return sensors

    def get(self):
        sensors_url = url + '/sensors'
        response = requests.request("GET", sensors_url, headers=headers, params=querystring)
        last_url = response.links.get('last')['url']
        print("Crawl Sensor pages")
        start_time = time.time()
        temp_urls = []
        page = 0
        # second loop to measure time correctly
        while True:
            temp_url = sensors_url + "?limit=100&page={}".format(page)
            temp_urls.append(temp_url)
            page += 1
            if temp_url == last_url:
                break
        # for temp_url in tqdm(temp_urls, total=len(temp_urls),
        #                   unit=' Processing Sensor pages'):
        #     self.fetch(temp_url)
        with ThreadPool(cpu) as pool:
            for _ in tqdm(pool.imap_unordered(self.fetch, temp_urls), total=len(temp_urls),
                          unit=' Processing Sensor pages'):
                pass
        pool.close()
        pool.join()
        end_time = time.time()
        print("Crawl-Result: {} Sensor pages | {} Sensors | {} Seconds".format(page, len(self.sensors),
                                                                               end_time - start_time))
        return self.sensors


class SensorStatistics:
    sensor_statistics = {}

    @staticmethod
    def process(data):
        statistics = {}
        for statistic in data['statistics']:
            statistics[statistic['phenomenon']['name']] = dict(unit=[statistic['phenomenon']['unit']],
                                                               max=[statistic['max']], avg=[statistic['avg']],
                                                               min=[statistic['min']],
                                                               measurements=[statistic['measurements']],
                                                               tracks=[statistic['tracks']], users=[statistic['users']],
                                                               sensors=[statistic['sensors']])
        return statistics

    @classmethod
    def fetch(cls, sensor):
        global counter
        statistics_url = url + '/sensors/{}/statistics'.format(sensor)
        try:
            statistics = file_management.get_response(statistics_url).json()
            cls.sensor_statistics[sensor] = cls.process(statistics)
            counter += 1
        except ValueError or AttributeError as err:
            print(err)
            pass

    def get(self, sensors):
        global counter
        counter = 0
        start_time = time.time()
        print("Crawl Sensor-Statistics")

        # for sensor in tqdm(sensors, total=len(sensors),
        #                    unit=' Processing Envirocar Sensor Statistics'):
        #     self.fetch(sensor)
        with ThreadPool(cpu) as pool:
            for _ in tqdm(pool.imap_unordered(self.fetch, sensors), total=len(sensors),
                          unit=' Processing Envirocar Sensors'):
                pass
        pool.close()
        pool.join()
        end_time = time.time()
        print("Crawl-Result: {} Sensor-Statistics | {} Seconds".format(counter, end_time - start_time))
        return self.sensor_statistics


class ECData(object):
    def __init__(self, all_parameters_min: bool = False, all_parameters_max: bool = False,
                 exc_av_statistics: bool = False, exc_track_statistics: bool = False, exc_track_measurements=False,
                 exc_sensors_and_stats=False):

        self.exc_av_statistics = exc_av_statistics
        self.exc_sensors_and_stats = exc_sensors_and_stats
        self.all_parameters_min = all_parameters_min
        self.all_parameters_max = all_parameters_max
        self.exc_track_statistics = exc_track_statistics
        self.exc_track_measurements = exc_track_measurements
        self.phenomenons = None
        self.sensors = None
        self.sensors_statistics = None
        self.average_statistics = None
        self.tracks = None
        self.tracks_statistics = None
        self.tracks_measurements = None

    def get_data(self, track_data: [] = None):
        # Todo Rework this damn thing by time (when time is given!)!

        if self.all_parameters_min:
            self.phenomenons = Phenomenons().get()
            self.sensors = Sensors().get()
            self.sensors_statistics = SensorStatistics().get(self.sensors)
            self.sensors = Merge().sensors_and_statistics(self.sensors, self.sensors_statistics)
            self.average_statistics = dict()
            self.average_statistics['vehicle_type'] = AverageStatistics().av_vehicle_type_statistics(self.sensors,
                                                                                                     self.phenomenons)
            self.average_statistics['manufacturer'] = AverageStatistics().av_manufacturer_statistics(self.sensors,
                                                                                                     self.phenomenons)
            pass
        elif self.all_parameters_max:
            self.phenomenons = Phenomenons().get()
            self.sensors = Sensors().get()
            self.sensors_statistics = SensorStatistics().get(self.sensors)
            self.sensors = Merge().sensors_and_statistics(self.sensors,
                                                          self.sensors_statistics)
            tracks = Tracks().get()
            tracks = Repair().repair_tracks(self.sensors, tracks)
            self.tracks = tracks
            self.sensors = Merge().sensors_and_tracks(self.sensors, tracks)
            self.tracks = tracks
            self.average_statistics = dict()
            self.average_statistics['vehicle_type'] = AverageStatistics().av_vehicle_type_statistics(
                self.sensors, self.phenomenons)
            tracks_statistics = TrackStatistics().get(tracks=tracks)
            pass
        elif self.exc_av_statistics:
            self.phenomenons = Phenomenons().get()
            self.sensors = Sensors().get()
            self.sensors_statistics = SensorStatistics().get(self.sensors)
            self.sensors = Merge().sensors_and_statistics(self.sensors,
                                                          self.sensors_statistics)
            self.average_statistics = dict()
            self.average_statistics['vehicle_type'] = AverageStatistics().av_vehicle_type_statistics(
                self.sensors, self.phenomenons)
            self.average_statistics['manufacturer'] = AverageStatistics().av_manufacturer_statistics(
                self.sensors, self.phenomenons)
        elif self.exc_sensors_and_stats:
            self.sensors = Sensors().get()
            self.sensors_statistics = SensorStatistics().get(self.sensors)
            pass
        elif self.exc_track_statistics and track_data is not None:
            # Getting Track statistics
            if len(track_data) > 0 and type(track_data) == list and type(track_data[0]) == str:
                tracks_statistics = TrackStatistics().get(tracks=track_data)
            pass
        elif self.exc_track_measurements:
            self.phenomenons = Phenomenons().get()
            self.sensors = Sensors().get()
            tracks = Tracks().get()
            tracks = Repair().repair_tracks(self.sensors, tracks)
            self.tracks = tracks
            track_data = []
            for track in tracks:
                track_data.append(track)
            if len(track_data) > 0 and type(track_data) == list and type(track_data[0]) == str:
                self.tracks_measurements = TrackMeasurements().get(tracks=track_data)
            pass
        return self
