import os
import sys
from collections import OrderedDict
from itertools import zip_longest

import nltk
from deepmerge import always_merger
from sty import fg
from tqdm import tqdm

from openfuelservice.server.db_import.envirocar.objects import SensorObject
from openfuelservice.server.db_import.models import CarfuelDataCarModel, EnvirocarSensorModel, WikiCarModel
from openfuelservice.server.drivers.misc_driver import EnvirocarWikiMatcher, CarFuelDataWikiMatcher
from openfuelservice.server.utils.database.queries import Wikipedia, Envirocar, CarFuelData
from openfuelservice.server.utils.misc.data_handling import save_positive_brand_intents, save_negative_brand_intents, \
    powerset, save_fixed_brand_matches
from openfuelservice.server import fixed_matches


def ask_yes_no(question: str, default='yes') -> bool or None:
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False, "c": None}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: {}".format(default))

    while True:
        choice = str(input('{}   |   {}'.format(question, prompt)).lower())
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' or 'c' for cancel"
                             "(or 'y' or 'n').\n")


def ask_for_matches(old_matches: {}, car_name: str) -> [] or None:
    reused_matches = []
    print(fg.red + "Select an entry from the List or enter a valid Wiki Hash:" + fg.rs)
    print(str("r: return picked matches"))
    print(str('a: abort'))
    print(str('c: clear selection'))
    counter = None
    while True:
        if old_matches.__len__() <= 0:
            pass
        elif counter == None:
            counter = 0
            for match in old_matches:
                print(str(counter) + ':' + ' ' + str(match) + ': ' + str(old_matches[match]))
                counter += 1
        choice = input(
            fg.green + 'Picked matches for ' + fg.rs + fg.yellow + car_name + fg.rs + fg.green + ': {} | Input choice: '.format(
                str(reused_matches)) + fg.rs)
        if choice == 'r':
            return reused_matches
        elif choice == 'a':
            return {}
        elif choice == 'c':
            reused_matches = []
            pass
        elif choice is None:
            pass
        elif len(choice) > 6:
            hashes = [choice.strip('"').strip("'")]
            wiki_cars = Wikipedia().get_cars_by_hashes(hashes)
            wiki_car: WikiCarModel
            [reused_matches.append(wiki_car.wiki_name) for wiki_car in wiki_cars]
            pass
        else:
            try:
                if int(choice) <= len(old_matches):
                    counter = 0
                    for match in old_matches:
                        if counter == int(choice):
                            reused_matches.extend(old_matches[match])
                            break
                        else:
                            counter += 1
                    pass
                else:
                    sys.stdout.write("\nPlease provide a valid selection.\n")
            except Exception:
                sys.stdout.write(fg.red + "\nPlease provide a valid selection.\n" + fg.rs)
                pass


def ask_real_wiki_hash(brand_name: str, non_wiki_car: str, wiki_hashes=[]) -> [WikiCarModel] or None:
    hashes = []
    hashes.extend(wiki_hashes)
    while True:
        wiki_cars = Wikipedia().get_cars_by_hashes(hashes)
        print("\nWiki Cars so far:", str(wiki_cars))
        choice = str(input(
            fg.green + '\nProvide with more wiki hashes one by one and end with enter for {} {}: '.format(brand_name,
                                                                                                          non_wiki_car) + fg.rs))
        choice = choice.strip('"')
        if choice is not None and len(choice) > 6:
            hashes.append(choice)
        elif choice == '':
            wiki_cars = Wikipedia().get_cars_by_hashes(hashes)
            return wiki_cars if wiki_cars is not None else []
        elif choice == 'none':
            return []
        else:
            sys.stdout.write("\nPlease provide valid wiki hashes or write none.\n")


def translate_car_collection(car_collection):
    translated_car_collection = {}
    for car in car_collection:
        if type(car) == EnvirocarSensorModel:
            car: EnvirocarSensorModel
            year = car.construction_year
            carName = car.car_model.casefold().strip() + ' ' + str(year).strip()
            uniqueCarName = car.car_model.casefold().strip() + str(year).strip()
            if uniqueCarName not in translated_car_collection:
                translated_car_collection[uniqueCarName] = []
                translated_car_collection[uniqueCarName].append(car)
        elif type(car) == CarfuelDataCarModel:
            car: CarfuelDataCarModel
            carName = car.model
            carDescription = car.description
            combinedName = carName + ' ' + carDescription
            year = car.year
            if combinedName.casefold() not in translated_car_collection:
                translated_car_collection[combinedName] = []
                translated_car_collection[combinedName].append(car)
    translated_car_collection = OrderedDict(sorted(translated_car_collection.items(), key=lambda t: t[0]))
    return translated_car_collection


class FixedMatchingAssessment(object):
    def __init__(self, envirocar: bool = False, carfueldata: bool = False, matchedData: bool = False):
        envirocarSensorsInDB = Envirocar().get_sensors(ordered=True) if envirocar else []
        cfdCarsInDB = CarFuelData().get_cfd_data(ordered=True) if carfueldata else []
        self.combinedCars = {}
        always_merger.merge(self.combinedCars, envirocarSensorsInDB)
        always_merger.merge(self.combinedCars, cfdCarsInDB)
        self.processedCars = dict()
        self.old_manufacturer_matches = {}
        self.total_progress = None

    def assess(self):
        self.total_progress = tqdm(total=len(self.combinedCars), unit=' Manufacturers Progress')
        for manufacturer in self.combinedCars:
            self.old_manufacturer_matches = {}
            answer = ask_yes_no('\nAssess brand: {}?'.format(manufacturer))
            if answer:
                carCollection = translate_car_collection(self.combinedCars[manufacturer])
                self.assessCarCollection(manufacturer=manufacturer, carColletion=carCollection)
            self.total_progress.update(+1)

    def assessCarCollection(self, manufacturer: str, carColletion):
        manufacturer_cars_progress = tqdm(total=len(carColletion), unit=' Manufacturer Cars Progress')
        for car_name in carColletion:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(self.total_progress)
            print(manufacturer_cars_progress)
            car = carColletion[car_name][0]
            if type(car) == EnvirocarSensorModel:
                car: EnvirocarSensorModel
                year = car.construction_year
                carName = car.car_model.casefold().strip() + ' ' + str(year).strip()
                uniqueCarName = car.car_model.casefold().strip() + str(year).strip()
                if uniqueCarName not in self.processedCars:
                    self.processedCars[uniqueCarName] = []
                    carWikiHashes = car.wiki_hashes
                    self.assessCar(manufacturer=manufacturer, year=year, carName=carName, carWikiHashes=carWikiHashes,
                                   uniqueCarName=uniqueCarName)
            elif type(car) == CarfuelDataCarModel:
                car: CarfuelDataCarModel
                carName = car.model
                carDescription = car.description
                combinedName = carName + ' ' + carDescription
                year = car.year
                if combinedName.casefold() not in self.processedCars:
                    self.processedCars[combinedName.casefold()] = []
                    carWikiHashes = car.wiki_hashes
                    self.assessCar(manufacturer=manufacturer, year=year, carName=combinedName,
                                   carWikiHashes=carWikiHashes, uniqueCarName=combinedName)
            manufacturer_cars_progress.update(+1)

    def assessCar(self, manufacturer: str, year: int, carName: str, carWikiHashes: [], uniqueCarName: str):
        wikiCars = Wikipedia().get_cars_by_hashes(hashes=carWikiHashes) if len(carWikiHashes) > 0 else []
        process = True
        if fixed_matches is not None and manufacturer in fixed_matches and uniqueCarName in fixed_matches[manufacturer]:
            process = ask_yes_no('\nCar already in fixed Matches. Assess car: {}?'.format(carName))
            old_matches = fixed_matches[manufacturer][uniqueCarName]
            self.old_manufacturer_matches[uniqueCarName] = []
            self.old_manufacturer_matches[uniqueCarName].extend(old_matches)
        if process:
            print(fg.yellow + '\nProcessing {} with car: {}'.format(manufacturer, carName) + fg.rs)
            finalCars = []
            old_matches = ask_for_matches(self.old_manufacturer_matches, car_name=carName)
            [wikiCars.append(old_match) for old_match in old_matches]
            for wikiCar in wikiCars:
                choice = ask_yes_no(
                    question=fg.green + "\nValid Match? {} ===> {}".format(
                        manufacturer + ' ' + carName + ' ' + str(year), wikiCar) + fg.rs)
                if choice:
                    finalCars.append(wikiCar)
                    pass
                elif choice == False:
                    wikiCars.remove(wikiCar)
                    pass
                elif choice is None:
                    print("\nSkip: {}".format(wikiCar))
            self.old_manufacturer_matches[uniqueCarName] = []
            self.old_manufacturer_matches[uniqueCarName].extend(finalCars)
            save_fixed_brand_matches(manufacturer=manufacturer, wikiCarNames=finalCars, uniqueCarName=uniqueCarName)


class AnnMatchingRefinement(object):
    def __init__(self, brand_limit: int = None, envirocar: bool = True, carfueldata: bool = True):
        # TODO e.g. unself them!
        self.matched_envirocar_data = EnvirocarWikiMatcher()
        self.matched_cfd_data = CarFuelDataWikiMatcher()
        if envirocar:
            self.matched_envirocar_data = EnvirocarWikiMatcher().match(brand_limit=brand_limit)
        if carfueldata:
            self.matched_cfd_data = CarFuelDataWikiMatcher().match(brand_limit=brand_limit)
        self.missing_cars = dict()
        self.matched_cars = dict()
        self.order_missing_cars()
        self.order_matched_cars()

    def order_missing_cars(self):
        missing_ec_car: SensorObject
        missing_cfd_car: CarfuelDataCarModel
        for missing_ec_car, missing_cfd_car in zip_longest(self.matched_envirocar_data.missed_matches,
                                                           self.matched_cfd_data.missed_matches,
                                                           fillvalue=None):
            if missing_ec_car is not None:
                ec_manufacturer = missing_ec_car.car_manufacturer
                if ec_manufacturer not in self.missing_cars:
                    self.missing_cars[ec_manufacturer] = dict()
                ec_car = missing_ec_car.car_model
                if ec_car not in self.missing_cars[ec_manufacturer]:
                    self.missing_cars[ec_manufacturer][ec_car] = []
                self.missing_cars[ec_manufacturer][ec_car].append(missing_ec_car)

            if missing_cfd_car is not None:
                cfd_manufacturer = missing_cfd_car.manufacturer
                if cfd_manufacturer not in self.missing_cars:
                    self.missing_cars[cfd_manufacturer] = dict()
                cfd_car = missing_cfd_car.model
                if cfd_car not in self.missing_cars[cfd_manufacturer]:
                    self.missing_cars[cfd_manufacturer][cfd_car] = []
                self.missing_cars[cfd_manufacturer][cfd_car].append(missing_cfd_car)

    def order_matched_cars(self):
        matched_ec_car: SensorObject
        matched_cfd_car: CarfuelDataCarModel
        for matched_ec_car, matched_cfd_car in zip_longest(self.matched_envirocar_data.matched_cars,
                                                           self.matched_cfd_data.matched_cars,
                                                           fillvalue=None):
            if matched_ec_car is not None:
                ec_manufacturer = matched_ec_car.car_manufacturer
                if ec_manufacturer not in self.matched_cars:
                    self.matched_cars[ec_manufacturer] = dict()
                ec_car = matched_ec_car.car_model
                if ec_car not in self.matched_cars[ec_manufacturer]:
                    self.matched_cars[ec_manufacturer][ec_car] = []
                self.matched_cars[ec_manufacturer][ec_car].append(matched_ec_car)

            if matched_cfd_car is not None:
                cfd_manufacturer = matched_cfd_car.manufacturer
                if cfd_manufacturer not in self.matched_cars:
                    self.matched_cars[cfd_manufacturer] = dict()
                cfd_car = matched_cfd_car.model
                if cfd_car not in self.matched_cars[cfd_manufacturer]:
                    self.matched_cars[cfd_manufacturer][cfd_car] = []
                self.matched_cars[cfd_manufacturer][cfd_car].append(matched_cfd_car)

    def assess_matched_cars(self):
        processed_cars = dict()
        for manufacturer in self.matched_cars:
            choice = ask_yes_no(question="Assess Manufacturer {}?".format(manufacturer))
            if choice == True:
                if manufacturer not in processed_cars:
                    processed_cars[manufacturer] = dict()
                matched_cars = self.matched_cars[manufacturer]
                matched_cars = OrderedDict(sorted(matched_cars.items(), key=lambda t: t[0]))
                for name_object in matched_cars:
                    for matched_car in matched_cars[name_object]:
                        if type(matched_car) == EnvirocarSensorModel:
                            matched_car: EnvirocarSensorModel
                            car_name = matched_car.car_model
                            car_name_lower = car_name.casefold()
                            year = matched_car.construction_year
                            if car_name_lower not in processed_cars[manufacturer]:
                                processed_cars[manufacturer][car_name_lower] = []
                                wiki_hashes = matched_car.wiki_hashes
                                wiki_cars = Wikipedia().get_cars_by_hashes(hashes=wiki_hashes)
                                wiki_car: WikiCarModel
                                names_to_save = []
                                names_to_save.append(car_name)
                                names_to_save.append(str(year))
                                names_to_save.append(car_name_lower)
                                for wiki_car in wiki_cars:
                                    wiki_car_name = wiki_car.wiki_name
                                    choice = ask_yes_no(
                                        question=fg.green + "Valid Match? {} ===> {}".format(
                                            manufacturer + ' ' + car_name + ' ' + str(year), wiki_car_name) + fg.rs)
                                    if choice == True:
                                        wiki_name_powerset = powerset(nltk.word_tokenize(wiki_car_name))
                                        [wiki_name_powerset.extend(name) for name in names_to_save]
                                        wiki_name_powerset.append(wiki_car_name)
                                        for power in wiki_name_powerset:
                                            if power.casefold() == manufacturer.casefold():
                                                wiki_name_powerset.remove(power)
                                        wiki_name_powerset = sorted(set(wiki_name_powerset))
                                        save_positive_brand_intents(brand_name=manufacturer, wiki_name=wiki_car_name,
                                                                    patterns=wiki_name_powerset)
                                        pass
                                    elif choice == False:
                                        save_negative_brand_intents(brand_name=manufacturer, wiki_name=wiki_car_name,
                                                                    patterns=[car_name])
                                        real_wiki_cars = ask_real_wiki_hash(brand_name=manufacturer,
                                                                            non_wiki_car=car_name + ' ' + str(year))
                                        real_wiki_car: WikiCarModel
                                        real_wiki_names = [real_wiki_car.wiki_name for real_wiki_car in real_wiki_cars]

                                        for wiki_name in real_wiki_names:
                                            choice = ask_yes_no(
                                                question="Valid Match? {} ===> {}".format(
                                                    manufacturer + ' ' + car_name + ' ' + str(year),
                                                    wiki_name))
                                            if choice == True:
                                                wiki_name_powerset = powerset(nltk.word_tokenize(wiki_car_name))
                                                [wiki_name_powerset.extend(name) for name in names_to_save]
                                                for power in wiki_name_powerset:
                                                    if power.casefold() == manufacturer.casefold():
                                                        wiki_name_powerset.remove(power)
                                                wiki_name_powerset = sorted(set(wiki_name_powerset))
                                                save_positive_brand_intents(brand_name=manufacturer,
                                                                            wiki_name=wiki_name,
                                                                            patterns=wiki_name_powerset)
                                                pass
                                            elif choice is None or choice is False:
                                                print("Skip: {}".format(wiki_name))
                                    elif choice is None:
                                        print("Skip: {}".format(wiki_car_name))
                        elif type(matched_car) == CarfuelDataCarModel:
                            matched_car: CarfuelDataCarModel
                            car_name = matched_car.model
                            car_name_lower = car_name.casefold()
                            if car_name_lower not in processed_cars[manufacturer]:
                                processed_cars[manufacturer][car_name_lower] = []
                                wiki_hashes = matched_car.wiki_hashes
                                wiki_cars = Wikipedia().get_cars_by_hashes(hashes=wiki_hashes)
                                names_to_save = []
                                names_to_save.append(matched_car.model)
                                names_to_save.append(matched_car.description)
                                names_to_save.append(str(matched_car.year))
                                for wiki_car in wiki_cars:
                                    wiki_car_name = wiki_car.wiki_name
                                    choice = ask_yes_no(
                                        question=fg.green + "Valid Match? {} {} {} ===> {}".format(
                                            manufacturer + ' ' + car_name,
                                            matched_car.description,
                                            str(matched_car.year),
                                            wiki_car_name) + fg.rs)
                                    if choice == True:
                                        wiki_name_powerset = powerset(nltk.word_tokenize(wiki_car_name))
                                        [wiki_name_powerset.extend(name) for name in names_to_save]
                                        wiki_name_powerset.append(wiki_car_name)
                                        for power in wiki_name_powerset:
                                            if power.casefold() == manufacturer.casefold():
                                                wiki_name_powerset.remove(power)
                                        wiki_name_powerset = sorted(set(wiki_name_powerset))
                                        save_positive_brand_intents(brand_name=manufacturer, wiki_name=wiki_car_name,
                                                                    patterns=wiki_name_powerset)
                                        pass
                                    elif choice == False:
                                        save_negative_brand_intents(brand_name=manufacturer, wiki_name=wiki_car_name,
                                                                    patterns=[car_name])
                                        real_wiki_cars = ask_real_wiki_hash(brand_name=manufacturer,
                                                                            non_wiki_car=car_name + ' ' + matched_car.description + ' ' + str(
                                                                                matched_car.year))

                                        real_wiki_car: WikiCarModel
                                        real_wiki_names = [real_wiki_car.wiki_name for real_wiki_car in real_wiki_cars]
                                        for wiki_name in real_wiki_names:
                                            choice = ask_yes_no(
                                                question=fg.green + "Valid Match? {} {} {} ===> {}".format(
                                                    manufacturer + ' ' + car_name, matched_car.description,
                                                    str(matched_car.year),
                                                    wiki_name) + fg.rs)
                                            if choice == True:
                                                wiki_name_powerset = powerset(nltk.word_tokenize(wiki_car_name))
                                                [wiki_name_powerset.extend(name) for name in names_to_save]
                                                wiki_name_powerset.append(wiki_car_name)
                                                for power in wiki_name_powerset:
                                                    if power.casefold() == manufacturer.casefold():
                                                        wiki_name_powerset.remove(power)
                                                wiki_name_powerset = sorted(set(wiki_name_powerset))
                                                save_positive_brand_intents(brand_name=manufacturer,
                                                                            wiki_name=wiki_name,
                                                                            patterns=wiki_name_powerset)
                                                pass
                                            elif choice is None or choice is False:
                                                print("Skip: {}".format(wiki_name))
                                        pass
                                    elif choice is None:
                                        print("Skip: {}".format(wiki_car_name))

    def assess_missing_cars(self):
        processed_cars = dict()
        for manufacturer in self.missing_cars:
            choice = ask_yes_no(question="Assess Manufacturer {}?".format(manufacturer))
            if choice == True:
                if manufacturer not in processed_cars:
                    processed_cars[manufacturer] = dict()
                missing_cars = self.missing_cars[manufacturer]
                missing_cars = OrderedDict(sorted(missing_cars.items(), key=lambda t: t[0]))
                for name_object in missing_cars:
                    for missing_car in missing_cars[name_object]:
                        if type(missing_car) == EnvirocarSensorModel:
                            missing_car: EnvirocarSensorModel
                            car_name = missing_car.car_model
                            car_name_lower = car_name.casefold()
                            year = missing_car.construction_year
                            if car_name_lower not in processed_cars[manufacturer]:
                                processed_cars[manufacturer][car_name_lower] = []
                                real_wiki_cars = ask_real_wiki_hash(brand_name=manufacturer,
                                                                    non_wiki_car=car_name + ' ' + str(year))
                                real_wiki_car: WikiCarModel
                                real_wiki_names = [real_wiki_car.wiki_name for real_wiki_car in real_wiki_cars]
                                names_to_save = []
                                names_to_save.append(car_name)
                                names_to_save.append(str(year))
                                names_to_save.append(car_name_lower)
                                for wiki_name in real_wiki_names:
                                    choice = ask_yes_no(
                                        question="Valid Match? {} ===> {}".format(manufacturer + ' ' + car_name,
                                                                                  wiki_name))
                                    if choice == True:
                                        wiki_name_powerset = powerset(nltk.word_tokenize(wiki_name))
                                        [wiki_name_powerset.extend(name) for name in names_to_save]
                                        wiki_name_powerset.append(wiki_name)
                                        for power in wiki_name_powerset:
                                            if power.casefold() == manufacturer.casefold():
                                                wiki_name_powerset.remove(power)
                                        wiki_name_powerset = sorted(set(wiki_name_powerset))
                                        save_positive_brand_intents(brand_name=manufacturer, wiki_name=wiki_name,
                                                                    patterns=wiki_name_powerset)
                                        pass
                                    elif choice is None or choice is False:
                                        print("Skip: {}".format(wiki_name))
                        elif type(missing_car) == CarfuelDataCarModel:
                            missing_car: CarfuelDataCarModel
                            car_name = missing_car.model
                            car_name_lower = car_name.casefold()
                            if car_name_lower not in processed_cars[manufacturer]:
                                processed_cars[manufacturer][car_name_lower] = []
                                real_wiki_cars = ask_real_wiki_hash(brand_name=manufacturer,
                                                                    non_wiki_car=car_name + ' ' + missing_car.description + ' ' + str(
                                                                        missing_car.year))
                                real_wiki_car: WikiCarModel
                                real_wiki_names = [real_wiki_car.wiki_name for real_wiki_car in real_wiki_cars]
                                names_to_save = []
                                names_to_save.append(missing_car.model)
                                names_to_save.append(missing_car.description)
                                names_to_save.append(str(missing_car.year))
                                for wiki_name in real_wiki_names:
                                    choice = ask_yes_no(
                                        question="Valid Match? {} {} {} ===> {}".format(manufacturer + ' ' + car_name,
                                                                                        missing_car.description,
                                                                                        str(missing_car.year),
                                                                                        wiki_name))
                                    if choice == True:
                                        wiki_name_powerset = powerset(nltk.word_tokenize(wiki_name))
                                        [wiki_name_powerset.extend(name) for name in names_to_save]
                                        wiki_name_powerset.append(wiki_name)
                                        for power in wiki_name_powerset:
                                            if power.casefold() == manufacturer.casefold():
                                                wiki_name_powerset.remove(power)
                                        wiki_name_powerset = sorted(set(wiki_name_powerset))
                                        save_positive_brand_intents(brand_name=manufacturer, wiki_name=wiki_name,
                                                                    patterns=wiki_name_powerset)
                                        pass
                                    elif choice is None or choice is False:
                                        print("Skip: {}".format(wiki_name))
