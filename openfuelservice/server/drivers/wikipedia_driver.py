"""Plan to crawl a car name database. Compare the car name db to the envirocar data. Categorize the models.
    Calculate the consumption, co2 per km/h and km. Calculate the values with min, avera, max.
    In the End ship the car model names with category consumption"""
import hashlib
import re
import time
from multiprocessing.dummy import Pool as ThreadPool

import requests
import urllib3
import wikipediaapi
from deepmerge import always_merger
from tqdm import tqdm
from wikipediaapi import WikipediaPage

from openfuelservice.server import ofs_settings, category_list, car_brands, verbose
from openfuelservice.server.db_import.models import WikiCarModel
from openfuelservice.server.db_import.wikipedia.objects import CarObject, CarCategoryObject, WikiCarPageTextObject
from openfuelservice.server.utils.database.queries import Wikipedia
from openfuelservice.server.utils.misc.file_management import get_response, find_values_in_json

cpu = ofs_settings['general']['cpu']

vehicle_categories = category_list['car_categories']


class ProcessWikipediaCars:
    category_objects = dict()
    counter = 0
    current_category_member = ""
    brands_list = dict()
    vehicles_list = dict()
    brands_aliases_list = dict()
    ignore_list = dict()

    def __init__(self):
        self.brands_list = car_brands['brands']
        self.vehicles_list = car_brands['vehicles']
        self.brands_aliases_list = car_brands['aliases']
        self.ignore_list = car_brands['ignore_list']

    def check_ignore_list(self, wiki_name: str):
        if wiki_name in self.ignore_list:
            return True
        return False

    def check_vehicles_list(self, wiki_name: str):
        if wiki_name in self.vehicles_list:
            model_brand = self.vehicles_list[wiki_name]['brand']
            model_name = self.vehicles_list[wiki_name]['name']
            return model_brand, model_name
        else:
            return '', ''

    def check_brands_aliases(self, short_name: str, wiki_name: str):
        for brand in self.brands_aliases_list:
            for alias in self.brands_aliases_list[brand]:
                if short_name.strip().lower() == alias.strip().lower():
                    model_name = wiki_name.replace(short_name, "").strip()
                    if len(model_name) > 0:
                        startswith = model_name[0]
                        endswith = model_name[-1:]
                    else:
                        startswith = ""
                        endswith = ""
                    if startswith == '-' or startswith == '/':
                        model_name = model_name[1:]
                    if startswith == '(' and endswith == ')':
                        return '', ''
                    return brand, model_name
        return '', ''

    def check_brand(self, short_name: str, wiki_name: str, brands_list):
        if short_name in brands_list:
            for brand in brands_list:
                if short_name in brand:
                    if re.search(r'\b{}\b'.format(brand), wiki_name):
                        model_name = wiki_name.replace(brand, "").strip()
                        model_brand = brand.strip()
                        if model_name is not "":
                            startswith = model_name[0]
                            endswith = model_name[-1:]
                            if startswith == '-' or startswith == '/':
                                model_name = model_name[1:]
                            if startswith == '(' and endswith == ')':
                                return '', ''
                            return model_brand, model_name
                        else:
                            return '', ''
                    cleaned_wiki_name = re.sub("[0-9]", " ", wiki_name)
                    cleaned_wiki_name = re.sub("[/]", "", cleaned_wiki_name)
                    cleaned_wiki_name = re.sub("[-]", " ", cleaned_wiki_name)
                    if re.search(r'\b{}\b'.format(brand), cleaned_wiki_name.strip()):
                        model_name = wiki_name.replace(brand, "").strip()
                        model_brand = brand.strip()
                        if model_name is not "":
                            startswith = model_name[0]
                            endswith = model_name[-1:]
                            if startswith == '-' or startswith == '/':
                                model_name = model_name[1:]
                            if startswith == '(' and endswith == ')':
                                return '', ''
                            return model_brand, model_name
                        else:
                            return '', ''
        return '', ''

    def process_category(self, category_member: dict()):
        category_member_string = category_member.__str__()
        ignore_check = self.check_ignore_list(wiki_name=category_member_string)
        if ignore_check:
            return ''
        short_name = category_member.__str__()
        for char in range(len(category_member_string)):
            model_brand, model_name = self.check_vehicles_list(wiki_name=category_member_string)
            if model_brand != '' and model_name != '':
                if model_brand not in self.category_objects:
                    self.category_objects[model_brand] = dict()
                if model_name not in self.category_objects[model_brand]:
                    self.category_objects[model_brand][model_name] = dict()
                self.category_objects[model_brand][model_name]['wiki_name'] = category_member_string
                return ""

            model_brand, model_name = self.check_brands_aliases(short_name=short_name, wiki_name=category_member_string)
            if model_brand != '' and model_name != '':
                if model_brand not in self.category_objects:
                    self.category_objects[model_brand] = dict()
                if model_name not in self.category_objects[model_brand]:
                    self.category_objects[model_brand][model_name] = dict()
                self.category_objects[model_brand][model_name]['wiki_name'] = category_member_string
                return ''

            model_brand, model_name = self.check_brand(short_name=short_name, wiki_name=category_member_string,
                                                       brands_list=self.brands_list)
            if model_brand != '' and model_name != '':
                if model_brand not in self.category_objects:
                    self.category_objects[model_brand] = dict()
                if model_name not in self.category_objects[model_brand]:
                    self.category_objects[model_brand][model_name] = dict()
                self.category_objects[model_brand][model_name]['wiki_name'] = category_member_string
                return ''
            elif len(short_name) > 1:
                short_name = short_name[:-1]
            else:
                if verbose:
                    print("Missing brand for car: {}".format(category_member_string))
                return ""

    def parse_cars(self, car_brands: dict(), category_member: str, category_members: dict(), page_language: str):
        post_processed_categories = dict()
        for brand in car_brands:
            if brand not in post_processed_categories:
                post_processed_categories[brand] = dict()
            for car in car_brands[brand]:
                post_processed_categories[brand][car] = []
                wiki_name = car_brands[brand][car]['wiki_name']
                car_name = re.sub(r"[-()\\\"#/@;:<>{}`+=~|.!?,]", " ", car)
                post_processed_categories[brand][car].append(CarObject(
                    hash_id=hashlib.md5(
                        (str(wiki_name).strip() + str(category_member).strip() + str(page_language).strip()).encode(
                            encoding='utf-8',
                            errors='ignore')).hexdigest(),
                    brand_name=brand,
                    car_name=car_name,
                    category_short_eu=category_member,
                    wiki_name=wiki_name,
                    page_language=page_language
                ))
        return post_processed_categories

    def parse_category(self, categories):
        wiki_car_categories = dict()
        category_objects = []
        for category in categories:
            for sub_category in categories[category]['category_names']:
                wiki_wiki = wikipediaapi.Wikipedia(language='de', timeout=None)
                if "Category" in sub_category:
                    wiki_wiki = wikipediaapi.Wikipedia(language='en', timeout=None)
                page: WikipediaPage = wiki_wiki.page(sub_category)
                page_language: WikipediaPage = page.__getattr__('language')

                page_py_category_members = page.categorymembers
                if category not in wiki_car_categories and len(page_py_category_members) > 0:
                    wiki_car_categories[category] = dict()
                    wiki_car_categories[category][page_language] = page_py_category_members
                if page_language not in wiki_car_categories[category]:
                    wiki_car_categories[category][page_language] = page_py_category_members
                elif len(page_py_category_members) > 0:
                    wiki_car_categories[category][page_language].update(page_py_category_members)
                else:
                    print("Category: {} is empty".format(sub_category))
            category_objects.append(CarCategoryObject(
                category_name_de=categories[category]['de'],
                category_name_en=categories[category]['en'],
                category_short_eu=category,
            ))
        return wiki_car_categories, category_objects

    def process_category_page(self, category_members: dict(), category: str):
        missed_counter = len(category_members)
        post_processed_category = dict()
        # for member in category_members:
        #     self.process_category(member)
        for page_language in category_members:
            with ThreadPool(cpu) as pool:
                for _ in pool.imap_unordered(self.process_category, category_members[page_language]):
                    pass
            pool.close()
            pool.join()
            result = (self.parse_cars(car_brands=self.category_objects, category_member=category,
                                      category_members=category_members,
                                      page_language=page_language))
            always_merger.merge(post_processed_category, result)
            self.category_objects.clear()
            missed_counter -= self.counter
        return post_processed_category


class ProcessWikipediaCarTexts(object):
    def __init__(self, filter_brand: str = None):
        self.filter_brand = None
        self.wiki_cars: [] = Wikipedia().get_cars_by_brand(filter_brand=filter_brand)
        self.wikicar_page_texts_in_db = Wikipedia().get_wikicar_page_texts(filter_brand=filter_brand, ordered=True)

    def process_wikicar_text(self, page_text, wiki_name, wikicar_brand, wikicar_model,
                             page_language, category_short_eu) -> WikiCarPageTextObject:
        return WikiCarPageTextObject(
            wiki_name=wiki_name,
            brand_name=wikicar_brand,
            car_name=wikicar_model,
            page_text=page_text,
            page_language=page_language,
            category_short_eu=category_short_eu
        )

    def fetch_wikicar_text_manually(self, language: str, title: str):
        splitted_title = title.split()
        reformatted_title = None
        for word in splitted_title:
            if reformatted_title is None:
                reformatted_title = word
            else:
                reformatted_title += '%20' + word
        try:
            page_text: str = None
            url = 'https://{}.wikipedia.org/w/api.php?action=query&prop=extracts&titles={}&explaintext=1&format=json'.format(
                language, reformatted_title)
            json_response: str = get_response(url=url).text
            texts = find_values_in_json(id='extract', json_repr=json_response)
            for text_element in texts:
                if page_text == None:
                    page_text = text_element + ' '
                else:
                    page_text += text_element + ' '
            return page_text.strip()
        except Exception as err:
            if type(err) == requests.exceptions.ConnectionError or type(
                    err) == urllib3.exceptions.MaxRetryError or type(err) == urllib3.exceptions.NewConnectionError:
                for t in tqdm(range(0, 120), unit=' Wikipedia overloaded. Waiting a little'):
                    time.sleep(1)
                self.fetch_wikicar_text_manually(language, title)
            else:
                print(err)
                print("Could not access or find json data")
            return ""

    def fetch_wikicar_text(self, page_language: str, wiki_name: str, wikicar_brand: str,
                           wikicar_model: str, category_short_eu: str, dummy: bool = False) -> WikiCarPageTextObject:
        page_text = ""
        if not dummy:
            try:
                wiki_wiki = wikipediaapi.Wikipedia(language=page_language, timeout=None)
                wiki_page = wiki_wiki.page(title=wiki_name)
                page_text = wiki_page.text
            except Exception as err:
                if type(err) == requests.exceptions.ConnectionError or type(
                        err) == urllib3.exceptions.MaxRetryError or type(err) == urllib3.exceptions.NewConnectionError:
                    for t in tqdm(range(0, 120), unit=' Wikipedia overloaded. Waiting a little'):
                        time.sleep(1)
                else:
                    self.fetch_wikicar_text(page_language, wiki_name, wikicar_brand, wikicar_model, category_short_eu)
            if len(page_text) == 0:
                page_text = self.fetch_wikicar_text_manually(language=page_language, title=wiki_name)
        return self.process_wikicar_text(page_text=page_text,
                                         wiki_name=wiki_name,
                                         wikicar_brand=wikicar_brand,
                                         wikicar_model=wikicar_model,
                                         page_language=page_language,
                                         category_short_eu=category_short_eu)

    def get_wikicar_texts(self, dummy: bool = False) -> {}:
        wiki_car: WikiCarModel
        wikicar_texts = dict()
        for wiki_car in self.wiki_cars:
            wiki_name = wiki_car.wiki_name
            page_text = ""
            if wiki_name in self.wikicar_page_texts_in_db and self.wikicar_page_texts_in_db[
                wiki_name].page_text is not None and len(self.wikicar_page_texts_in_db[wiki_name].page_text) > 0:
                page_text = self.wikicar_page_texts_in_db[wiki_name].page_text
            elif page_text is None or len(page_text) < 1:
                wikicar_brand: str = wiki_car.brand_name
                wikicar_model: str = wiki_car.car_name
                category_short_eu: str = wiki_car.category_short_eu
                page_language: str = wiki_car.page_language
                wikicar_texts[wiki_name] = self.fetch_wikicar_text(page_language=page_language,
                                                                   wiki_name=wiki_name,
                                                                   wikicar_brand=wikicar_brand,
                                                                   wikicar_model=wikicar_model,
                                                                   category_short_eu=category_short_eu,
                                                                   dummy = dummy)
        return wikicar_texts


def get_wikipedia_car_data() -> []:
    results = dict()
    wiki_car_categories, category_objects = ProcessWikipediaCars().parse_category(vehicle_categories)

    for category_member in tqdm(wiki_car_categories, total=len(wiki_car_categories),
                                unit=' Processing Wikipedia Categories'):
        car_brands: dict() = (
            ProcessWikipediaCars().process_category_page(wiki_car_categories[category_member], category_member))

        for brand in car_brands:
            if brand not in results:
                results[brand] = dict()
            for car in car_brands[brand]:
                if car not in results[brand]:
                    results[brand][car] = []
                for car_object in car_brands[brand][car]:
                    results[brand][car].append(car_object)
        car_brands.clear()
    return category_objects, results
