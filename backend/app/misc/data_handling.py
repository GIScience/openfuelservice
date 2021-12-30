import logging
from typing import Dict, Union

from app.core.config import settings

logger = logging.getLogger(__name__)


def check_manufacturer(manufacturer_to_check: str) -> Union[str, None]:
    cleaned_manufacturer_to_check: str = manufacturer_to_check.casefold().strip()
    aliases: Dict = settings.CAR_BRANDS.get("aliases", {})
    brands: Dict = settings.CAR_BRANDS.get("brands", {})
    manufacturer: str
    for manufacturer in aliases:
        if cleaned_manufacturer_to_check == manufacturer.casefold().strip():
            return manufacturer
        for sub_alias in aliases[manufacturer]:
            if cleaned_manufacturer_to_check in sub_alias.casefold().strip():
                return manufacturer
    for manufacturer in brands:
        if cleaned_manufacturer_to_check == manufacturer.casefold().strip():
            return manufacturer
        if manufacturer_to_check == manufacturer:
            return manufacturer
    logger.debug(f"Manufacturer: {manufacturer_to_check} not in known list.")
    return None


# def get_negative_brand_intents(brand_name_or_path: str or PosixPath) -> dict() or None:
#     if type(brand_name_or_path) == PosixPath:
#         try:
#             return json.load(open(brand_name_or_path.absolute(), 'r'))
#         except Exception as err:
#             print("Couldn't open json file:", brand_name_or_path.absolute())
#             print(err)
#     elif type(brand_name_or_path) == str:
#         manual_intents_path = file_folder.joinpath('models').joinpath('manual_intents')
#         intents_files = list(manual_intents_path.glob('*_negative.json'))
#         for file in intents_files:
#             intent_name = file.name[:-len('_negative.json')]
#             if intent_name == brand_name_or_path:
#                 try:
#                     return json.load(open(file.absolute(), 'r'))
#                 except Exception as err:
#                     print("Couldn't open json file:", file.absolute())
#                     print(err)
#     return None
#
#
# def get_positive_brand_intents(brand_name_or_path: str or PosixPath) -> dict() or None:
#     if type(brand_name_or_path) == PosixPath:
#         try:
#             return json.load(open(brand_name_or_path.absolute(), 'r'))
#         except Exception as err:
#             print("Couldn't open json file:", brand_name_or_path.absolute())
#             print(err)
#     elif type(brand_name_or_path) == str:
#         manual_intents_path = file_folder.joinpath('models').joinpath('manual_intents')
#         intents_files = list(manual_intents_path.glob('*_positive.json'))
#         for file in intents_files:
#             intent_name = file.name[:-len('_positive.json')]
#             if intent_name == brand_name_or_path:
#                 try:
#                     return json.load(open(file.absolute(), 'r'))
#                 except Exception as err:
#                     print("Couldn't open json file:", file.absolute())
#                     print(err)
#     return None
#
#
# def get_negative_car_patterns(brand_name: str, wiki_name: str) -> list():
#     manufacturer_positive_intents = get_negative_brand_intents(brand_name)
#     car_negative_intents: list() = list()
#     if manufacturer_positive_intents is not None:
#         for intent in manufacturer_positive_intents['intents']:
#             if intent['tag'] == wiki_name:
#                 car_negative_intents = intent['patterns']
#                 break
#     if car_negative_intents is not None:
#         return car_negative_intents
#     else:
#         return []
#
#
# def get_positive_car_patterns(brand_name: str, wiki_name: str) -> list():
#     manufacturer_positive_intents = get_positive_brand_intents(brand_name)
#     car_positive_intents: list() = list()
#     if manufacturer_positive_intents is not None:
#         for intent in manufacturer_positive_intents['intents']:
#             if intent['tag'] == wiki_name:
#                 car_positive_intents = intent['patterns']
#                 break
#     if car_positive_intents is not None:
#         return car_positive_intents
#     else:
#         return []
#
#
# def powerset(iterable) -> []:
#     return_list = []
#     set_normal = list(iterable)
#     set_lower = [x.casefold() for x in set_normal]
#     set_title = [x.title() for x in set_normal]
#     set_capital = [x.capitalize() for x in set_normal]
#     set_caps = [x.upper() for x in set_normal]
#     powerset_normal = chain.from_iterable(combinations(set_normal, r) for r in range(len(set_normal) + 1))
#     powerset_lower = chain.from_iterable(combinations(set_lower, r) for r in range(len(set_lower) + 1))
#     powerset_title = chain.from_iterable(combinations(set_title, r) for r in range(len(set_title) + 1))
#     powerset_capital = chain.from_iterable(combinations(set_capital, r) for r in range(len(set_capital) + 1))
#     powerset_caps = chain.from_iterable(combinations(set_caps, r) for r in range(len(set_caps) + 1))
#
#     for normal, lower, title, capital, caps in zip_longest(powerset_normal, powerset_lower, powerset_title,
#                                                            powerset_capital, powerset_caps, fillvalue=''):
#         sentence_normal = ""
#         sentence_lower = ""
#         sentence_title = ""
#         sentence_capital = ""
#         sentence_caps = ""
#         if len(normal) > 0:
#             for word in normal:
#                 sentence_normal += ' ' + word
#             return_list.append(sentence_normal.strip())
#         if len(lower) > 0:
#             for word in lower:
#                 sentence_lower += ' ' + word
#             return_list.append(sentence_lower.strip())
#         if len(title) > 0:
#             for word in title:
#                 sentence_title += ' ' + word
#             return_list.append(sentence_title.strip())
#         if len(capital) > 0:
#             for word in capital:
#                 sentence_capital += ' ' + word
#             return_list.append(sentence_capital.strip())
#         if len(caps) > 0:
#             for word in caps:
#                 sentence_caps += ' ' + word
#             return_list.append(sentence_caps.strip())
#     return sorted(set(return_list))
#
# def save_fixed_brand_matches(manufacturer: str, wikiCarNames: [], uniqueCarName: str):
#     originalFixedMatchesPath = basedir.joinpath('categories').joinpath('fixed_matches.yml')
#     originalFixedMatches = yaml.safe_load(open(originalFixedMatchesPath, encoding='utf-8'))
#     originalFixedMatches = originalFixedMatches if originalFixedMatches is not None else dict()
#     if manufacturer in originalFixedMatches:
#         fixedManufacturerMatches = originalFixedMatches[manufacturer]
#     else:
#         originalFixedMatches[manufacturer] = dict()
#         fixedManufacturerMatches = dict()
#     for wikiCarName in wikiCarNames:
#         if uniqueCarName in fixedManufacturerMatches:
#             if wikiCarName not in fixedManufacturerMatches[uniqueCarName]:
#                 fixedManufacturerMatches[uniqueCarName].append(wikiCarName)
#         else:
#             fixedManufacturerMatches[uniqueCarName] = []
#             fixedManufacturerMatches[uniqueCarName].append(wikiCarName)
#     originalFixedMatches[manufacturer] = fixedManufacturerMatches
#     try:
#         with open(originalFixedMatchesPath.absolute(), 'w') as outfile:
#             json.dump(originalFixedMatches, outfile)
#     except Exception as err:
#         print("Couldn't write fixed matching to file:", originalFixedMatchesPath.absolute())
#         print(err)

#
# def save_negative_brand_intents(brand_name: str, wiki_name: str, patterns: []) -> dict() or None:
#     intent_path = file_folder.joinpath('models').joinpath('manual_intents').joinpath(
#         '{}_negative.json'.format(brand_name))
#     original_brand_intents = get_negative_brand_intents(brand_name_or_path=intent_path)
#     if original_brand_intents is not None:
#         data_updated = False
#         for intent in original_brand_intents['intents']:
#             if intent['tag'] == wiki_name:
#                 original_patterns = intent['patterns']
#                 patterns_set = set(patterns)
#                 original_patterns_set = set(original_patterns)
#                 combined_patterns = list(original_patterns_set | patterns_set)
#                 intent['patterns'] = combined_patterns
#                 data_updated = True
#         if not data_updated:
#             new_data = dict()
#             new_data['tag'] = wiki_name
#             new_data['patterns'] = patterns
#             original_brand_intents['intents'].append(new_data)
#             data_updated = True
#     else:
#         original_brand_intents = dict()
#         new_data = dict()
#         new_data['tag'] = wiki_name
#         new_data['patterns'] = patterns
#         original_brand_intents['intents'] = []
#         original_brand_intents['intents'].append(new_data)
#     try:
#         if original_brand_intents is not None:
#             with open(intent_path.absolute(), 'w') as outfile:
#                 json.dump(original_brand_intents, outfile)
#     except Exception as err:
#         print("Couldn't write json intent file:", intent_path.absolute())
#         print(err)
#
#
# def save_positive_brand_intents(brand_name: str, wiki_name: str, patterns: []) -> dict() or None:
#     intent_path = file_folder.joinpath('models').joinpath('manual_intents').joinpath(
#         '{}_positive.json'.format(brand_name))
#     original_brand_intents = get_positive_brand_intents(brand_name_or_path=intent_path)
#     patterns = [pattern for pattern in patterns if pattern.casefold() != brand_name.casefold()]
#     if original_brand_intents is not None:
#         data_updated = False
#         for intent in original_brand_intents['intents']:
#             if intent['tag'] == wiki_name:
#                 original_patterns = intent['patterns']
#                 patterns_set = set(patterns)
#                 original_patterns_set = set(original_patterns)
#                 combined_patterns = list(original_patterns_set | patterns_set)
#                 intent['patterns'] = combined_patterns
#                 data_updated = True
#         if not data_updated:
#             new_data = dict()
#             new_data['tag'] = wiki_name
#             new_data['patterns'] = patterns
#             original_brand_intents['intents'].append(new_data)
#             data_updated = True
#     else:
#         original_brand_intents = dict()
#         new_data = dict()
#         new_data['tag'] = wiki_name
#         new_data['patterns'] = patterns
#         original_brand_intents['intents'] = []
#         original_brand_intents['intents'].append(new_data)
#     try:
#         if original_brand_intents is not None:
#             with open(intent_path.absolute(), 'w') as outfile:
#                 json.dump(original_brand_intents, outfile)
#     except Exception as err:
#         print("Couldn't write json intent file:", intent_path.absolute())
#         print(err)
#
# def clean_manufacturer_list(manufacturers_to_check: []) -> []:
#     cleaned_list = []
#     for manufacturer in manufacturers_to_check:
#         real_manufacturer = check_manufacturer(manufacturer)
#         if real_manufacturer != "":
#             cleaned_list.append(real_manufacturer)
#     return cleaned_list
