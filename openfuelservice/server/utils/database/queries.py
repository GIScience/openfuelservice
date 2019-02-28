from openfuelservice.server import db, allowed_fuel_types
from openfuelservice.server.db_import.models import EnvirocarSensorModel, WikiCarModel, MatchedWikiEnvirocarModel, \
    CarfuelDataCarModel, WikiCarPageTextModel, CarCategoryModel, EnvirocarSensorStatisticModel
from openfuelservice.server.utils.misc.data_handling import clean_manufacturer_list


def get_relevevant_brands() -> list:
    cfd_brands = CarFuelData().get_cfd_brands()
    cfd_brands = clean_manufacturer_list(manufacturers_to_check=cfd_brands)
    ec_brands = Envirocar().get_sensor_brands()
    ec_brands = clean_manufacturer_list(manufacturers_to_check=ec_brands)
    for brand in cfd_brands:
        if brand not in ec_brands:
            ec_brands.append(brand)
    return ec_brands


def get_brands(carfueldata: bool, envirocar: bool, wikicar: bool) -> {}:
    """Function for the brands API Call. Should not return Envirocar Brands. They are not clean enough!"""
    brands_processed = {}
    brands = []
    cfd_brands = []
    ec_brands = []
    if carfueldata:
        cfd_brands = CarFuelData().get_cfd_brands(lower=False)
        cfd_brands = clean_manufacturer_list(manufacturers_to_check=cfd_brands)
        for brand in cfd_brands:
            if brand not in brands_processed:
                brands.append(brand)
                brands_processed[brand] = ""
    if envirocar:
        ec_brands = Envirocar().get_sensor_brands()
        ec_brands = clean_manufacturer_list(manufacturers_to_check=ec_brands)
        for brand in ec_brands:
            if brand not in brands_processed:
                brands.append(brand)
                brands_processed[brand] = ""
    if wikicar:
        wikicar_brands = Wikipedia().get_brands()
        wikicar_brands = clean_manufacturer_list(manufacturers_to_check=wikicar_brands)
        for brand in wikicar_brands:
            if brand not in brands_processed:
                brands.append(brand)
                brands_processed[brand] = ""
    return brands


def get_cars_by_category(brand: str, carfueldata: bool = True, matched_only: bool = True, wiki_cars: bool = True):
    cars = {}
    cars_return = {}
    if carfueldata:
        cfd_query = CarFuelData().get_cfd_cars(brand=brand, matched_only=True) if matched_only else \
            CarFuelData().get_cfd_cars(brand=brand, matched_only=False)
        cfd_car: CarfuelDataCarModel
        for cfd_car in cfd_query:
            wiki_hashes = cfd_car.wiki_hashes
            wiki_car_objects = Wikipedia().get_cars_by_hashes(hashes=wiki_hashes)
            wiki_car: WikiCarModel
            wiki_categories = [wiki_car.category_short_eu for wiki_car in wiki_car_objects]
            if str(cfd_car.model) not in cars:
                cars[cfd_car.model] = {}
                cars[cfd_car.model]['categories'] = []
            [cars[cfd_car.model]['categories'].append(category) for category in wiki_categories if
             category not in cars[cfd_car.model]['categories']]
    if wiki_cars:
        wiki_query = Wikipedia().get_cars_by_brand(filter_brand=brand)
        wiki_car: WikiCarModel
        for wiki_car in wiki_query:
            wiki_car: WikiCarModel
            categories = wiki_car.category_short_eu
            if str(wiki_car.car_name) not in cars:
                cars[wiki_car.car_name] = {}
                cars[wiki_car.car_name]['categories'] = []
            [cars[wiki_car.car_name]['categories'].append(category) for category in categories if
             category not in cars[wiki_car.car_name]['categories']]
    cars_return['cars'] = cars
    return cars_return


def get_car_ids(brand, source):
    cars = {}
    if source == 'cfd':
        query = CarFuelData().get_cfd_cars(brand=brand, matched_only=True)
        car: CarfuelDataCarModel
        for car in query:
            model = car.model.strip()
            cleaned_model_name = " "
            year = str(car.year)
            last_digits = str(year)[-2:]
            description = car.description.strip()
            fuel_type = car.fuel_type
            wiki_hashes = car.wiki_hashes
            cfd_hash_id = car.hash_id
            tokenized_model_name = model.split(',')
            if len(tokenized_model_name) > 1:
                for word in tokenized_model_name:
                    word = word.strip()
                    if str(year) in word:
                        continue
                    elif str(last_digits) in word and 'my' in word.lower():
                        continue
                    elif 'my' in word.lower() and len(word) <= 4:
                        continue
                    else:
                        cleaned_model_name = cleaned_model_name + ' ' + word
            else:
                if 'MY' + str(year) in model:
                    cleaned_model_name = model.strip('MY' + str(year))
                if 'MY' + str(last_digits) in model:
                    cleaned_model_name = model.strip('MY' + str(last_digits))
            cleaned_model_name = cleaned_model_name.strip() if len(cleaned_model_name.strip()) > 0 else model
            if fuel_type not in allowed_fuel_types:
                continue
            if wiki_hashes is None or len(wiki_hashes) <= 0:
                continue
            for processed_car in cars:
                if processed_car.lower() == cleaned_model_name.lower():
                    cleaned_model_name = processed_car
            if cleaned_model_name not in cars:
                cars[cleaned_model_name] = {}
                cars[cleaned_model_name]['all'] = []
            cars[cleaned_model_name]['all'].append(cfd_hash_id)
            if year not in cars[cleaned_model_name]:
                cars[cleaned_model_name][year] = {}
                cars[cleaned_model_name][year]['all'] = []
            cars[cleaned_model_name][year]['all'].append(cfd_hash_id)
            if description not in cars[cleaned_model_name][year]:
                cars[cleaned_model_name][year][description] = []
                cars[cleaned_model_name][year][description].append(cfd_hash_id)
    return cars


def get_cars(brand: str, carfueldata: bool = True, matched_only: bool = True, wiki_cars: bool = True):
    cars = {}
    if carfueldata:
        cfd_query = CarFuelData().get_cfd_cars(brand=brand, matched_only=True) if matched_only else \
            CarFuelData().get_cfd_cars(brand=brand, matched_only=False)
        cfd_car: CarfuelDataCarModel
        for cfd_car in cfd_query:
            wiki_hashes = cfd_car.wiki_hashes
            wiki_car_objects = Wikipedia().get_cars_by_hashes(hashes=wiki_hashes)
            wiki_car: WikiCarModel
            wiki_categories = [wiki_car.category_short_eu for wiki_car in wiki_car_objects]
            if str(cfd_car.model) not in cars:
                cars[cfd_car.model] = {}
                cars[cfd_car.model]['categories'] = []
            [cars[cfd_car.model]['categories'].append(category) for category in wiki_categories if
             category not in cars[cfd_car.model]['categories']]
    if wiki_cars:
        wiki_query = Wikipedia().get_cars_by_brand(filter_brand=brand)
        wiki_car: WikiCarModel
        for wiki_car in wiki_query:
            wiki_car: WikiCarModel
            categories = wiki_car.category_short_eu
            if str(wiki_car.car_name) not in cars:
                cars[wiki_car.car_name] = {}
                cars[wiki_car.car_name]['categories'] = []
            [cars[wiki_car.car_name]['categories'].append(category) for category in categories if
             category not in cars[wiki_car.car_name]['categories']]
    return cars


class Envirocar:
    def get_sensors(self, ordered: bool = False, with_wiki_hashes_only: bool = False) -> {} or []:
        db_entries: [] = db.session.query(EnvirocarSensorModel).all()
        if ordered:
            ordered_dict = dict()
            entry: EnvirocarSensorModel
            for entry in db_entries:
                brand_name = entry.car_manufacturer
                wiki_hashes_in_object = entry.wiki_hashes
                if brand_name not in ordered_dict:
                    ordered_dict[brand_name] = []
                if with_wiki_hashes_only and wiki_hashes_in_object is not None and len(wiki_hashes_in_object) > 0:
                    ordered_dict[brand_name] = []
                if not with_wiki_hashes_only:
                    ordered_dict[brand_name].append(entry)
            return ordered_dict
        elif with_wiki_hashes_only and not ordered:
            return_list = []
            for entry in db_entries:
                wiki_hashes_in_object = entry.wiki_hashes
                if wiki_hashes_in_object is not None and len(wiki_hashes_in_object) > 0:
                    return_list.append(entry)
            return return_list
        else:
            return db_entries

    def get_sensor_brands(self):
        brands = []
        query = db.session.query(EnvirocarSensorModel.car_manufacturer).all()
        model: EnvirocarSensorModel
        for model in query:
            manufacturer = model.car_manufacturer.lower()
            if manufacturer not in brands:
                brands.append(manufacturer)
        return brands

    def get_sensor_stats(self, sensor_id, first_only=False):
        if first_only:
            query = db.session.query(EnvirocarSensorStatisticModel).filter_by(sensor_id=sensor_id).first()
        else:
            query = db.session.query(EnvirocarSensorStatisticModel).filter_by(sensor_id=sensor_id).all()
        return query


class CarFuelData:
    def get_cfd_data(self, ordered: bool = False, with_wiki_hashes_only: bool = False) -> {} or []:
        db_entries: {} = (
            db.session.query(CarfuelDataCarModel).all())

        if ordered:
            ordered_dict = dict()
            entry: CarfuelDataCarModel
            for entry in db_entries:
                brand_name = entry.manufacturer
                wiki_hashes_in_object = entry.wiki_hashes
                if brand_name not in ordered_dict:
                    ordered_dict[brand_name] = []
                if with_wiki_hashes_only and wiki_hashes_in_object is not None and len(wiki_hashes_in_object) > 0:
                    ordered_dict[brand_name].append(entry)
                if not with_wiki_hashes_only:
                    ordered_dict[brand_name].append(entry)
            return ordered_dict
        elif with_wiki_hashes_only and not ordered:
            return_list = []
            for entry in db_entries:
                wiki_hashes_in_object = entry.wiki_hashes
                if wiki_hashes_in_object is not None and len(wiki_hashes_in_object) > 0:
                    return_list.append(entry)
            return return_list
        else:
            return db_entries

    def get_cfd_brands(self, lower: bool = True):
        brands = []
        query = db.session.query(CarfuelDataCarModel.manufacturer).all()
        model: CarfuelDataCarModel
        for model in query:
            if lower:
                manufacturer = model.manufacturer.lower()
            else:
                manufacturer = model.manufacturer
            if manufacturer not in brands:
                brands.append(manufacturer)
        return brands

    def get_cfd_cars(self, brand: str, matched_only: bool = False):
        return_cars = {}
        if matched_only:
            query = db.session.query(CarfuelDataCarModel).filter_by(manufacturer=brand).filter(
                CarfuelDataCarModel.wiki_hashes != None).all()
        else:
            query = db.session.query(CarfuelDataCarModel).filter_by(manufacturer=brand).all()
        return query

    def query_cfd_cars_all(self):
        query: list = (
            db.session.query(CarfuelDataCarModel).all())
        return query

    def get_cfd_categories(self, cfd_ids: []):
        return_categories = {}
        if cfd_ids is None:
            return return_categories
        for cfd_id in cfd_ids:
            if cfd_id not in return_categories:
                return_categories[cfd_id] = []
            db_entry: CarfuelDataCarModel = db.session.query(CarfuelDataCarModel).filter(CarfuelDataCarModel.hash_id == cfd_id).first()
            if db_entry is not None:
                wiki_hashes = db_entry.wiki_hashes
                categories = Wikipedia().get_categories_by_hashes(wiki_hashes=wiki_hashes)
                return_categories[cfd_id] = [category for category in categories if category not in return_categories[cfd_id]]
        return return_categories


class Wikipedia:

    def get_hashes_by_name(self, wiki_name: str):
        with db.session.no_autoflush:
            query = db.session.query(WikiCarModel).filter(WikiCarModel.wiki_name == wiki_name).all()
            model: WikiCarModel
            hashes = []
            for model in query:
                hashes.append(model.hash_id)
            return hashes

    def get_brands(self):
        brands = []
        query = db.session.query(WikiCarModel.brand_name).all()
        wikicarmodel: WikiCarModel
        for wikicarmodel in query:
            brand = wikicarmodel.brand_name
            if brand not in brands:
                brands.append(brand)
        return brands

    def get_hashes_by_wikiname(self, wiki_names: []) -> []:
        return_queries = []
        for wiki_name in wiki_names:
            db_entries: [WikiCarModel] = db.session.query(WikiCarModel).filter(
                WikiCarModel.wiki_name == wiki_name).all()
            if db_entries is not None:
                [return_queries.append(wiki_car_model.hash_id) for wiki_car_model in db_entries]
        return return_queries

    def get_cars_by_hashes(self, hashes: []):
        return_queries = []
        if hashes is None:
            return return_queries
        for hash in hashes:
            db_entry = db.session.query(WikiCarModel).filter(WikiCarModel.hash_id == hash).first()
            if db_entry is not None:
                return_queries.append(db_entry)
        return return_queries

    def get_categories_by_hashes(self, wiki_hashes: []):
        return_categories = []
        if wiki_hashes is None:
            return return_categories
        for wiki_hash in wiki_hashes:
            db_entry: WikiCarModel = db.session.query(WikiCarModel).filter(WikiCarModel.hash_id == wiki_hash).first()
            if db_entry is not None:
                return_categories.append(db_entry.category_short_eu)
        return return_categories

    def get_cars_by_brand(self, filter_brand: str = None):
        if filter_brand is None:
            db_entries = db.session.query(WikiCarModel).all()
        else:
            db_entries = db.session.query(WikiCarModel).filter(WikiCarModel.brand_name == filter_brand).all()
        return db_entries

    def get_wikicar_page_texts(self, filter_brand: str = None, ordered: bool = False) -> [] or dict():
        if filter_brand is None:
            db_entries = db.session.query(WikiCarPageTextModel).all()
        else:
            db_entries = db.session.query(WikiCarPageTextModel).filter(
                WikiCarPageTextModel.brand_name == filter_brand).all()
        if ordered:
            car_dict = dict()
            entry: WikiCarPageTextModel
            for entry in db_entries:
                wiki_name = entry.wiki_name
                if wiki_name not in car_dict:
                    car_dict[wiki_name] = entry
            return car_dict
        return db_entries

    def get_cars_ordered(self, use_wikiname: bool = False):
        car_dict = dict()
        db_entries = db.session.query(WikiCarModel).all()
        entry: WikiCarModel
        for entry in db_entries:
            brand_name = entry.brand_name
            car_name = entry.car_name
            if brand_name not in car_dict:
                car_dict[brand_name] = dict()
            if use_wikiname == True:
                car_name = entry.wiki_name
            if car_name not in car_dict[brand_name]:
                car_dict[brand_name][car_name] = []
            car_dict[brand_name][car_name].append(entry)
        return car_dict

    def get_cars_pure(self) -> []:
        db_entries = db.session.query(WikiCarModel).all()
        return db_entries

    def get_cars_per_manufacturer(self, manufacturer) -> []:
        query = db.session.query(WikiCarModel).filter(WikiCarModel.brand_name == manufacturer).all()
        return query

    def get_categories(self, ordered: bool = False) -> {} or []:
        query = db.session.query(CarCategoryModel).all()
        if ordered:
            categories = {}
            category: CarCategoryModel
            for category in query:
                category_dict = {}
                category_dict['short'] = category.category_short_eu
                category_dict['en'] = category.category_name_en
                category_dict['de'] = category.category_name_de
                categories[category.category_short_eu] = category_dict
            return categories
        return query


class Misc:

    def matched_cars(self):
        """
        Returns the matched cars.
        """
        query_return = []
        query = (
            db.session.query(
                MatchedWikiEnvirocarModel).join(
                WikiCarModel, WikiCarModel.hash_id == MatchedWikiEnvirocarModel.car_hash_id).all())
        return query
