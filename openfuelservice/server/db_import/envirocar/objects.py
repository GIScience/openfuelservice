class PhenomenonObject(object):
    def __init__(self, name, unit):
        self.name = name
        self.unit = unit


# TODO Add ARRAY's to sensors for each track etc????
class SensorObject(object):
    def __init__(self, sensor_id, sensor_type, car_model, fuel_type, construction_year, car_manufacturer, wiki_hashes):
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.car_model = car_model
        self.fuel_type = fuel_type
        self.construction_year = construction_year
        self.car_manufacturer = car_manufacturer
        self.wiki_hashes = wiki_hashes



class TrackObject(object):
    def __init__(self, track_id, sensor_id, track_length):
        """Track class to hold the track objects.

        :param track_id:
        :param sensor_id:
        :param track_length:
        """
        self.track_id = track_id
        self.sensor_id = sensor_id
        self.track_length = track_length


class SensorStatisticObject(object):
    def __init__(self, sensor_id, phenomenon_name, max, avg, min, numb_measurements, numb_tracks, numb_users,
                 numb_sensors):
        self.sensor_id = sensor_id
        self.phenomenon_name = phenomenon_name
        self.max = max
        self.avg = avg
        self.min = min
        self.numb_measurements = numb_measurements
        self.numb_tracks = numb_tracks
        self.numb_users = numb_users
        self.numb_sensors = numb_sensors


class TrackStatisticObject(object):
    def __init__(self, track_id, phenomenon_name, max, avg, min, numb_measurements, numb_tracks, numb_users,
                 numb_sensors):
        self.track_id = track_id
        self.phenomenon_name = phenomenon_name
        self.max = max
        self.avg = avg
        self.min = min
        self.numb_measurements = numb_measurements
        self.numb_tracks = numb_tracks
        self.numb_users = numb_users
        self.numb_sensors = numb_sensors


class TrackMeasurementObject(object):
    def __init__(self, track_measurement_id, track_id, sensor_id, phenomenon_name, phenomenon_value, date):
        self.track_measurement_id = track_measurement_id
        self.track_id = track_id
        self.sensor_id = sensor_id
        self.phenomenon_name = phenomenon_name
        self.phenomenon_value = phenomenon_value
        self.date = date


class TrackFeatureObject(object):
    def __init__(self, track_measurement_id, sensor_id, track_id, geom):
        self.track_measurement_id = track_measurement_id
        self.sensor_id = sensor_id
        self.track_id = track_id
        self.geom = geom



