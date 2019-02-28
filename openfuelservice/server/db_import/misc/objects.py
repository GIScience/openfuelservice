class MatchedWikiCarSensorObject(object):
    def __init__(self, sensor_id= None, car_hash_id = None, category_short_eu = None):
        self.sensor_id = sensor_id
        self.car_hash_id = car_hash_id
        self.category_short_eu = category_short_eu


class MatchedWikiCFDObject(object):
    def __init__(self, carfueldata_car_id= None, car_hash_id = None, category_short_eu = None):
        self.carfueldata_car_id = carfueldata_car_id
        self.car_hash_id = car_hash_id
        self.category_short_eu = category_short_eu