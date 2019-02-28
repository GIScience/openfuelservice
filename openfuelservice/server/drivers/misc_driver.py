import re
from multiprocessing.dummy import Pool as ThreadPool

import nltk
from fuzzywuzzy import fuzz
from sty import fg
from tqdm import tqdm

from openfuelservice.server import ofs_settings, car_brands, verbose, fixed_matches, create_app
from openfuelservice.server.db_import.envirocar.objects import SensorObject
from openfuelservice.server.db_import.models import CarfuelDataCarModel
from openfuelservice.server.utils.database.queries import Envirocar, CarFuelData, Wikipedia
from openfuelservice.server.utils.matching.tf.create_models import ManufacturerANNModelCollection
from openfuelservice.server.utils.misc.data_handling import powerset

manufacturer_aliases = car_brands['aliases']
manufacturers = car_brands['brands']
cpu = ofs_settings['general']['cpu']


# Todo Replace all old matching functions with the new model matchers
def check_name_for_year(string: str) -> int or None:
    # Only with latest cars. The data before have no date object and seldom a year in its name
    import datetime
    now = datetime.datetime.now()
    max_year = int(now.year)
    min_year = 1980
    search_year = max_year
    while True:
        if search_year < min_year:
            return None
        elif str(search_year) in string:
            return search_year
        else:
            search_year -= 1


def remove_double_words(string: str) -> str:
    return_words = []
    string_words = nltk.word_tokenize(string.casefold())
    [return_words.append(word) for word in string_words if '' + word + '' not in return_words]
    return_string = ' '.join(return_words)
    return return_string.strip()


def check_similarity(string1: str, string2: str) -> bool:
    year = check_name_for_year(string1)
    if year is not None:
        string1 = string1.replace(str(year), ' ').strip()
    # ??? Strip the brackets?
    string1_cleaned = re.sub("[\(\[].*?[\)\]]", "", string1).replace("-", " ").strip()
    string2_cleaned = re.sub("[\(\[].*?[\)\]]", "", string2).replace("-", " ").strip()
    string1 = string1.replace("-", " ").strip().casefold()
    string2 = string2.replace("-", " ").strip().casefold()
    if len(re.findall(r'\w+', string1)) <= 1 or len(re.findall(r'\w+', string2)) <= 1:
        return False
    elif len(re.findall(r'\w+', string1_cleaned)) <= 1 or len(re.findall(r'\w+', string2_cleaned)) <= 1:
        return False
    elif fuzz.ratio(string1, string2) > 90:
        return True
    elif fuzz.ratio(string1_cleaned, string2_cleaned) > 93:
        return True
    elif fuzz.token_sort_ratio(string1, string2) > 93:
        return True
    elif fuzz.token_sort_ratio(string1_cleaned, string2_cleaned) > 93:
        return True
    elif fuzz.token_set_ratio(string1, string2) > 93:
        return True
    elif fuzz.token_set_ratio(string1_cleaned, string2_cleaned) > 93:
        return True
    else:
        return False


def check_manufacturer(manufacturer_to_check: str) -> str:
    cleaned_manufacturer_to_check = manufacturer_to_check.casefold().strip()
    for manufacturer in manufacturer_aliases:
        if cleaned_manufacturer_to_check == manufacturer.casefold().strip():
            return manufacturer
        for alias in manufacturer_aliases[manufacturer]:
            if cleaned_manufacturer_to_check == alias.casefold().strip():
                return manufacturer
    for manufacturer in car_brands['brands']:
        if manufacturer_to_check == manufacturer.casefold().strip():
            return manufacturer
        if cleaned_manufacturer_to_check == manufacturer.casefold().strip():
            return manufacturer
    print("Couldn't find manufacturer {}".format(manufacturer_to_check))
    return ""


def check_fixed_matches(manufacturer: str, car_name: str, year: int) -> []:
    if manufacturer in fixed_matches:
        manufacturer_matches = fixed_matches[manufacturer]
        wiki_names = []
        for fixed_match in manufacturer_matches:
            if car_name.casefold() == fixed_match or car_name.casefold() + str(year) == fixed_match:
                for wiki_name in manufacturer_matches[fixed_match]:
                    wiki_names.append(wiki_name)
        return wiki_names


class WikiMatcher(object):

    def __init__(self, manufacturers: [] = None):
        self.collection = ManufacturerANNModelCollection()
        self.collection.load_models()

        if manufacturers == None:
            self.collection.initialize_models()
        else:
            self.collection.initialize_models(model_names=manufacturers)

    def find_wiki_hashes(self, wiki_name: str) -> []:
        matched_hashes = Wikipedia().get_hashes_by_name(wiki_name=wiki_name)
        return matched_hashes

    def match(self, manufacturer: str, car: str, matching_score: float = 0.99, complex_matching: bool = False) -> []:
        wikicar_hashes = list()
        matchings = []
        car_name_powerset = []
        year = check_name_for_year(car)
        car_without_year = ""
        if year is not None:
            car_without_year = car.replace(str(year), ' ').strip()
        car_name_powerset.extend(car_without_year)
        car_without_year = remove_double_words(car_without_year)
        car_name_powerset.extend(powerset([manufacturer, car]))
        matching = (self.collection.classify(manufacturer=manufacturer, car_name=car))
        for brand in matching:
            matchings.extend(matching[brand])
        if manufacturer in manufacturer_aliases:
            for alias in manufacturer_aliases[manufacturer]:
                car_name_powerset.extend(powerset([alias, car]))
        for power in car_name_powerset:
            sentence_length = len(nltk.word_tokenize(power))
            if sentence_length >= 2:
                matching = self.collection.classify(manufacturer=manufacturer, car_name=power)
                for brand in matching:
                    matchings.extend(matching[brand])
        for matching in matchings:
            matching: (())
            car_name_to_check = manufacturer + ' ' + car
            car_name_to_check_cleaned = car.replace(manufacturer, ' ')
            car_name_to_check_cleaned = car.replace(manufacturer.casefold(), ' ')
            car_name_to_check_cleaned = car.replace(manufacturer.capitalize(), ' ').strip()
            wiki_name = matching[0]
            wiki_name_cleaned = wiki_name.replace(manufacturer, ' ')
            wiki_name_cleaned = wiki_name.replace(manufacturer.casefold(), ' ')
            wiki_name_cleaned = wiki_name.replace(manufacturer.capitalize(), ' ').strip()
            words_in_wiki_name: [] = nltk.word_tokenize(wiki_name)
            score = matching[1]
            if score >= matching_score:
                matched_hashes: [] = self.find_wiki_hashes(wiki_name=wiki_name)
                for hash in matched_hashes:
                    if hash not in wikicar_hashes:
                        wikicar_hashes.append(hash)
                        if verbose:
                            print(fg.green + "Matched:" + fg.rs, car_name_to_check, '|', wiki_name, '|', 'Score:',
                                  fg.green + str(score) + fg.rs)
                pass
            elif complex_matching:
                if score >= matching_score - 0.06:
                    marker = True
                    for word in words_in_wiki_name:
                        word_lower = word.lower()
                        if word_lower not in car_name_to_check.lower():
                            marker = False
                    if marker == True:
                        matched_hashes: [] = self.find_wiki_hashes(wiki_name=wiki_name)
                        for hash in matched_hashes:
                            if hash not in wikicar_hashes:
                                wikicar_hashes.append(hash)
                                if verbose:
                                    print(fg.green + "Matched:" + fg.rs, car_name_to_check, '|', wiki_name, '|',
                                          'Score:',
                                          fg.green + str(score) + fg.rs)
                elif check_similarity(string1=car_name_to_check, string2=wiki_name):
                    matched_hashes: [] = self.find_wiki_hashes(wiki_name=wiki_name)
                    for hash in matched_hashes:
                        if hash not in wikicar_hashes:
                            wikicar_hashes.append(hash)
                            if verbose:
                                print(fg.yellow + "Exceptionally Matched:" + fg.rs, car_name_to_check, '|', wiki_name,
                                      '|',
                                      'Score:', fg.yellow + str(score) + fg.rs)
                elif check_similarity(string1=car_name_to_check_cleaned, string2=wiki_name):

                    matched_hashes: [] = self.find_wiki_hashes(wiki_name=wiki_name)
                    for hash in matched_hashes:
                        if hash not in wikicar_hashes:
                            wikicar_hashes.append(hash)
                            if verbose:
                                print(fg.yellow + "Exceptionally Matched:" + fg.rs, car_name_to_check, '|', wiki_name,
                                      '|',
                                      'Score:', fg.yellow + str(score) + fg.rs)
                elif check_similarity(string1=manufacturer + ' ' + (car_name_to_check_cleaned.strip()),
                                      string2=wiki_name):
                    matched_hashes: [] = self.find_wiki_hashes(wiki_name=wiki_name)
                    for hash in matched_hashes:
                        if hash not in wikicar_hashes:
                            wikicar_hashes.append(hash)
                            if verbose:
                                print(fg.yellow + "Exceptionally Matched:" + fg.rs, car_name_to_check, '|', wiki_name,
                                      '|',
                                      'Score:', fg.yellow + str(score) + fg.rs)
                elif manufacturer == 'Daihatsu' and score >= 0.4:
                    matched_hashes: [] = self.find_wiki_hashes(wiki_name=wiki_name)
                    for hash in matched_hashes:
                        if hash not in wikicar_hashes:
                            wikicar_hashes.append(hash)
                            if verbose:
                                print(fg.yellow + "Exceptionally Matched:" + fg.rs, car_name_to_check, '|', wiki_name,
                                      '|',
                                      'Score:', fg.yellow + str(score) + fg.rs)
                elif manufacturer == 'Audi' and score >= 0.85:  # Really? --> Problem are really wrong results sometimes
                    matched_hashes: [] = self.find_wiki_hashes(wiki_name=wiki_name)
                    for hash in matched_hashes:
                        if hash not in wikicar_hashes:
                            wikicar_hashes.append(hash)
                            if verbose:
                                print(fg.yellow + "Exceptionally Matched:" + fg.rs, car_name_to_check, '|', wiki_name,
                                      '|',
                                      'Score:', fg.yellow + str(score) + fg.rs)
                elif manufacturer == 'BMW' and score >= 0.97:
                    matched_hashes: [] = self.find_wiki_hashes(wiki_name=wiki_name)
                    for hash in matched_hashes:
                        if hash not in wikicar_hashes:
                            wikicar_hashes.append(hash)
                            if verbose:
                                print(fg.yellow + "Exceptionally Matched:" + fg.rs, car_name_to_check, '|', wiki_name,
                                      '|',
                                      'Score:', fg.yellow + str(score) + fg.rs)
                if manufacturer in manufacturer_aliases:
                    for alias in manufacturer_aliases[manufacturer]:
                        car_name_to_check_cleaned = car.replace(alias, ' ')
                        car_name_to_check_cleaned = car.replace(alias.casefold(), ' ')
                        car_name_to_check_cleaned = car.replace(alias.capitalize(), ' ').strip()
                        wiki_name_cleaned = wiki_name.replace(alias, ' ')
                        wiki_name_cleaned = wiki_name.replace(alias.casefold(), ' ')
                        wiki_name_cleaned = wiki_name.replace(alias.capitalize(), ' ').strip()
                        if check_similarity(string1=alias + ' ' + car_name_to_check, string2=wiki_name):
                            matched_hashes: [] = self.find_wiki_hashes(wiki_name=wiki_name)
                            for hash in matched_hashes:
                                if hash not in wikicar_hashes:
                                    wikicar_hashes.append(hash)
                                    if verbose:
                                        print(fg.yellow + "Exceptionally Matched:" + fg.rs, car_name_to_check, '|',
                                              wiki_name, '|',
                                              'Score:', fg.yellow + str(score) + fg.rs)
                        elif check_similarity(string1=alias + ' ' + car_name_to_check_cleaned,
                                              string2=wiki_name_cleaned):
                            matched_hashes: [] = self.find_wiki_hashes(wiki_name=wiki_name)
                            for hash in matched_hashes:
                                if hash not in wikicar_hashes:
                                    wikicar_hashes.append(hash)
                                    if verbose:
                                        print(fg.yellow + "Exceptionally Matched:" + fg.rs, car_name_to_check, '|',
                                              wiki_name, '|',
                                              'Score:', fg.yellow + str(score) + fg.rs)
            if len(wikicar_hashes) == 0 and verbose:
                print(fg.red + "Not Matched:" + fg.rs, car_name_to_check, '|', wiki_name, '|', 'Score:',
                      fg.red + str(score) + fg.rs)
        return wikicar_hashes


class EnvirocarWikiMatcher(object):
    def __init__(self, complex_matching=False):
        self.envirocar_data_in_db = Envirocar().get_sensors(ordered=True)
        self.wiki_matcher = None
        self.missed_matches = []
        self.matched_cars = []
        self.complex_matching = complex_matching

    def match_with_ann(self, brand, matching_score, car):
        car_name = car.car_model
        year = car.construction_year
        wiki_hashes: [] = self.wiki_matcher.match(manufacturer=brand, car=car_name,
                                                  matching_score=matching_score,
                                                  complex_matching=self.complex_matching)
        wiki_hashes.extend(self.wiki_matcher.match(manufacturer=brand, car=car_name + ' ' + str(year),
                                                   matching_score=matching_score - 0.03,
                                                   complex_matching=self.complex_matching))
        full_name = [brand, car_name, str(year)]
        car_name_powerset = powerset(full_name)
        car_name_powerset = [power for power in car_name_powerset if
                             len(nltk.word_tokenize(power)) >= len(nltk.word_tokenize(car_name))]
        car_name_powerset = [power for power in car_name_powerset if car_name in power]
        car_name_powerset = sorted(list(set(car_name_powerset)))
        for name in car_name_powerset:
            hashes = []
            hashes = self.wiki_matcher.match(manufacturer=brand, car=name, matching_score=matching_score - 0.03,
                                             complex_matching=self.complex_matching)
            for hash in hashes:
                wiki_hashes.extend(hash) if hash not in wiki_hashes else None

        if len(wiki_hashes) == 0:
            self.missed_matches.append(car)
        else:
            car.wiki_hashes = wiki_hashes
            self.matched_cars.append(car_name)
        return car

    def match(self, brand_limit: int = None, matching_score: float = 0.97, complex_matching: bool = False):
        brand_counter = 0
        progress = None
        print("\nMatching Envirocar Wikicar Data")
        if not verbose:
            progress = tqdm(total=len(self.envirocar_data_in_db), unit=' Matching Envirocar Brands')
        for brand in self.envirocar_data_in_db:
            if brand_limit is not None and brand_counter >= brand_limit:
                break
            car: SensorObject
            for car in self.envirocar_data_in_db[brand]:
                car_name = car.car_model
                year = car.construction_year
                wiki_names = check_fixed_matches(manufacturer=brand, car_name=car_name, year=year)
                wiki_hash_ids = Wikipedia().get_hashes_by_wikiname(wiki_names)
                car.wiki_hashes = wiki_hash_ids
                if len(wiki_hash_ids) == 0:
                    if self.wiki_matcher is None:
                        self.wiki_matcher = WikiMatcher(manufacturers=[brand])
                    car = self.match_with_ann(brand=brand, car=car, matching_score=matching_score)
                self.matched_cars.append(car)
            brand_counter += 1
            if not verbose:
                progress.update(+1)
            self.wiki_matcher = None
        if not verbose:
            progress.close()
        if verbose:
            for car in self.missed_matches:
                print('Missing:', str(car.car_manufacturer), str(car.car_model))
        return self


class CarFuelDataWikiMatcher(object):
    def __init__(self):
        self.cfd_data_in_db = CarFuelData().get_cfd_data(ordered=True)
        self.wiki_matcher = None
        self.missed_matches = []
        self.matched_cars = []
        self.matching_score = 1
        self.complex_matching = False
        self.app = create_app()

    def process_car(self, car: CarfuelDataCarModel):
        # Create app for multithreaded db querying
        with self.app.app_context():
            brand = car.manufacturer
            car_name = car.model
            car_description = car.description
            car_name_cleaned = None
            year = car.year
            comma_counter = 0
            character_counter = 0
            # Some car names got a comma in it. It is misleading a lot while matching
            for i in range(0, len(car_name)):
                character_counter += 1
                if car_name[i] == ",":
                    comma_counter += 1
            if comma_counter == 1 and character_counter > len(brand):
                car_name_cleaned = car_name.split(",")[0]

            wiki_hashes: [] = self.wiki_matcher.match(manufacturer=brand,
                                                      car=car_name if car_name_cleaned is None else car_name_cleaned,
                                                      matching_score=self.matching_score,
                                                      complex_matching=self.complex_matching)
            if len(wiki_hashes) == 0:
                wiki_hashes.extend(self.wiki_matcher.match(manufacturer=brand, car=car_name + ' ' + str(year),
                                                           matching_score=self.matching_score,
                                                           complex_matching=self.complex_matching))
            if len(wiki_hashes) == 0:
                wiki_hashes.extend(self.wiki_matcher.match(manufacturer=brand, car=car_name + ' ' + car_description,
                                                           matching_score=self.matching_score,
                                                           complex_matching=self.complex_matching))
            if len(wiki_hashes) == 0:
                wiki_hashes.extend(
                    self.wiki_matcher.match(manufacturer=brand, car=car_name + ' ' + car_description + ' ' + str(year),
                                            matching_score=self.matching_score, complex_matching=self.complex_matching))

            if len(wiki_hashes) == 0:
                min_search_string_size = len(nltk.word_tokenize(brand))
                search_string = ' '.join([brand, car_name if car_name_cleaned is None else car_name_cleaned])
                search_string_words = nltk.word_tokenize(search_string)
                while True:
                    if len(search_string_words) <= min_search_string_size:
                        break
                    temporary_search_string = " ".join(search_string_words)
                    wiki_hashes: [] = self.wiki_matcher.match(manufacturer=brand,
                                                              car=temporary_search_string,
                                                              complex_matching=self.complex_matching)
                    if len(wiki_hashes) > 0:
                        break
                    else:
                        search_string_words.pop()

            if len(wiki_hashes) == 0:
                self.missed_matches.append(car)
            else:
                car.wiki_hashes = wiki_hashes
                self.matched_cars.append(car)

    def match(self, brand_limit: int = None, matching_score: float = 0.97, complex_matching: bool = False):
        self.matching_score = matching_score
        self.complex_matching = complex_matching
        brand_counter = 0
        progress = None
        total_cars = 0
        print("\nMatching CarFuelData and Wikicar data")
        if not verbose:
            progress = tqdm(total=len(self.cfd_data_in_db) - 1, unit=' Matching Car Fuel data Cars and Wikicars')
        for brand in self.cfd_data_in_db:
            if brand_limit is not None and brand_counter >= brand_limit:
                break
            self.wiki_matcher = WikiMatcher(manufacturers=[brand])
            total_cars += len(self.cfd_data_in_db[brand])
            with ThreadPool(cpu) as pool:
                for _ in tqdm(pool.imap_unordered(self.process_car, self.cfd_data_in_db[brand]),
                              total=len(self.cfd_data_in_db[brand]),
                              unit=' Processing Cars for {}'.format(brand)):
                    pass
            pool.close()
            pool.join()
            brand_counter += 1
            if not verbose:
                progress.update(+1)
        if verbose:
            for car in self.missed_matches:
                print('Missing:', str(car.manufacturer), str(car.model))
        print('Matching Accuracy: {}/{}'.format(len(self.matched_cars), total_cars))
        return self
