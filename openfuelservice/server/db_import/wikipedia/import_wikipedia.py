import hashlib

from sqlalchemy.exc import IntegrityError
from tqdm import tqdm

from openfuelservice.server import db
from openfuelservice.server.db_import.models import CarCategoryModel, WikiCarModel, \
    EnvirocarAverageCategoryStatisticsModel, WikiCarPageTextModel
from openfuelservice.server.db_import.wikipedia.objects import CarCategoryObject, CarObject, WikiCarPageTextObject
from openfuelservice.server.statistics.objects import AverageEnviroCarCategoryStatisticObject


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


class WikipediaImporter:
    def __init__(self):
        self.car_categories = []
        self.car_objects = []
        self.av_category_statistics = []
        self.page_text_objects = []

    def store_car_category(self, car_category_object: CarCategoryObject):
        self.car_categories.append(CarCategoryModel(
            category_short_eu=car_category_object.category_short_eu,
            category_name_de=car_category_object.category_name_de,
            category_name_en=car_category_object.category_name_en,
        ))

    def store_car_object(self, car_object: CarObject):
        self.car_objects.append(WikiCarModel(
            hash_id=car_object.hash_id,
            wiki_name=car_object.wiki_name,
            category_short_eu=car_object.category_short_eu,
            brand_name=car_object.brand_name,
            car_name=car_object.car_name,
            page_id=car_object.page_id,
            page_language=car_object.page_language
        ))



    def store_wiki_car_page_text(self, page_text_object: WikiCarPageTextObject):
        wiki_name = page_text_object.wiki_name
        page_language = page_text_object.page_language
        self.page_text_objects.append(WikiCarPageTextModel(
            hash_id=hashlib.md5(
                (str(wiki_name).strip() +
                 str(page_language).strip()).encode(encoding='UTF-8', errors='ignore')).hexdigest(),
            wiki_name=wiki_name,
            brand_name=page_text_object.brand_name,
            car_name=page_text_object.car_name,
            page_language=page_language,
            page_text=page_text_object.page_text,
            category_short_eu=page_text_object.category_short_eu
        ))

    def import_car_categories(self, car_categories):
        for car_category in tqdm(car_categories, total=len(car_categories), unit=' Importing wikipedia Car Categories'):
            self.store_car_category(car_category)
        fallback_importer(self.car_categories)

    def import_car_objects(self, car_objects):
        for brand in tqdm(car_objects, unit=' Importing Car Brands', total=len(car_objects)):
            for car_object in car_objects[brand]:
                for car in range(0, len(car_objects[brand][car_object])):
                    self.store_car_object(car_objects[brand][car_object][car])
            fallback_importer(self.car_objects)
            self.car_objects = []



    def import_wiki_page_texts(self, page_texts: dict()):
        for wikicar in tqdm(page_texts, unit=' Importing Wiki Car Page Texts', total=len(page_texts)):
            self.store_wiki_car_page_text(page_text_object=page_texts[wikicar])
        fallback_importer(self.page_text_objects)
        self.page_text_objects = []
