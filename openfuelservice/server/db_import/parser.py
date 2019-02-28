from openfuelservice.server.db_import.agency_data.carfueldata.import_carfueldata import CarFuelDataImporter
from openfuelservice.server.db_import.countries.import_countries import CountryImporter
from openfuelservice.server.db_import.envirocar.import_envirocar import EnvirocarImporter
from openfuelservice.server.db_import.eurostat.import_eurostat import EurostatImporter
from openfuelservice.server.db_import.misc.import_misc import MatchedImporter, MiscImporter
from openfuelservice.server.db_import.wikipedia.import_wikipedia import WikipediaImporter
from openfuelservice.server.drivers.carfueldata_driver import LatestCars
from openfuelservice.server.drivers.envirocar_driver import ECData
from openfuelservice.server.drivers.misc_driver import EnvirocarWikiMatcher, CarFuelDataWikiMatcher


# TODO remove misc importer!

def parse_cfd(cfd_data: LatestCars or CarFuelDataWikiMatcher):
    print("\nImporting CarFuelData")
    if type(cfd_data) == LatestCars:
        cfd_data: LatestCars
        if len(cfd_data.cfd_objects_list) > 0:
            CarFuelDataImporter().import_cfd(cfd_data=cfd_data.cfd_objects_list)
    elif type(cfd_data) == CarFuelDataWikiMatcher:
        cfd_data: CarFuelDataWikiMatcher
        if len(cfd_data.matched_cars) > 0:
            CarFuelDataImporter().import_cfd(cfd_data=cfd_data.matched_cars)


def parse_eurostat(eurostat_data):
    print("\nImporting Eurostat data")
    for element in eurostat_data:
        if element == 'country_prices':
            EurostatImporter().import_countries(eurostat_data[element])
        if element == 'general_prices':
            EurostatImporter().import_general(eurostat_data[element])


def parse_envirocar(envirocar_data: ECData or EnvirocarWikiMatcher):
    """
    Standard parser for envirocar data. Processes the crawled data in objects and objects to models.
    The models are pushed to the db. The if conditions are designed to be object relational safe.
    Tracks statistics und tracks measurements are not included!
    :param envirocar_data:
    """
    if type(envirocar_data) == ECData:
        print("\nImporting envirocar data")
        if envirocar_data.phenomenons is not None:
            EnvirocarImporter().import_phenomenons(envirocar_data.phenomenons)
        if envirocar_data.sensors is not None:
            EnvirocarImporter().import_sensors(envirocar_data.sensors)
        if envirocar_data.sensors_statistics is not None and envirocar_data.sensors is not None:
            EnvirocarImporter().import_sensors_statistics(envirocar_data.sensors_statistics)
        if envirocar_data.tracks is not None and envirocar_data.sensors is not None:
            EnvirocarImporter().import_tracks(envirocar_data.tracks)
        if envirocar_data.tracks_statistics is not None and envirocar_data.sensors is not None:
            EnvirocarImporter().import_sensors_statistics(envirocar_data.sensors_statistics)
        if envirocar_data.average_statistics is not None:
            if 'vehicle_type' in envirocar_data.average_statistics:
                EnvirocarImporter().import_average_vehicle_type_statistics(
                    envirocar_data.average_statistics['vehicle_type'])
            if 'manufacturer' in envirocar_data.average_statistics:
                EnvirocarImporter().import_average_manufacturer_statistics(
                    envirocar_data.average_statistics['manufacturer'])
    elif type(envirocar_data) == EnvirocarWikiMatcher:
        print("\nImporting envirocar data")
        envirocar_data: EnvirocarWikiMatcher
        if len(envirocar_data.matched_cars) > 0:
            EnvirocarImporter().import_sensors(envirocar_data.matched_cars)


def parse_envirocar_advanced(envirocar_data: ECData):
    """
    Like parse_envirocar but the if conditions are not designed to be object relational safe!
    Tracks statistics und tracks measurements are included!

    :param envirocar_data: Dict holding the envirocar data
    """
    print("\nImporting envirocar data")
    if envirocar_data.phenomenons is not None:
        EnvirocarImporter().import_phenomenons(envirocar_data.phenomenons)
    if envirocar_data.sensors is not None:
        EnvirocarImporter().import_sensors(envirocar_data.sensors)
    if envirocar_data.sensors_statistics is not None:
        EnvirocarImporter().import_sensors_statistics(envirocar_data.sensors_statistics)
    if envirocar_data.tracks is not None:
        EnvirocarImporter().import_tracks(envirocar_data.tracks)
    if envirocar_data.tracks_statistics is not None:
        EnvirocarImporter().import_sensors_statistics(envirocar_data.sensors_statistics)
    if envirocar_data.average_statistics is not None:
        if 'vehicle_type' in envirocar_data.average_statistics:
            EnvirocarImporter().import_average_vehicle_type_statistics(
                envirocar_data.average_statistics['vehicle_type'])
        if 'manufacturer' in envirocar_data.average_statistics:
            EnvirocarImporter().import_average_manufacturer_statistics(
                envirocar_data.average_statistics['manufacturer'])
    if envirocar_data.tracks_measurements is not None:
        EnvirocarImporter().import_tracks_features(envirocar_data.tracks_measurements['features'])
        EnvirocarImporter().import_tracks_measurements(envirocar_data.tracks_measurements['measurements'])


def parse_countries(countries_data):
    print("\nImporting Country data")
    CountryImporter().import_countries(countries_data)
    pass


def parse_wikipedia(wikicar_categories=None, wikicar_objects=None, wikicar_texts: dict = None):
    if wikicar_categories:
        print("\nImporting Wikipedia car data")
        WikipediaImporter().import_car_categories(car_categories=wikicar_categories)
    if wikicar_objects:
        print("\nImporting Wikipedia car data")
        WikipediaImporter().import_car_objects(car_objects=wikicar_objects)
    if wikicar_texts:
        print("\nImporting Wikipedia car data")
        WikipediaImporter().import_wiki_page_texts(page_texts=wikicar_texts)


def parse_misc(matched_wikicar_envirocar=None, ec_av_category_stats=None, cfd_av_category_stats=None):
    print("\nImporting average category data")
    if matched_wikicar_envirocar:
        print("\nImporting matched car data")
        MatchedImporter().import_matched_wikicar_envirocar(matched_wikicar_envirocar)
    if ec_av_category_stats:
        MiscImporter().import_average_ec_category_stats(av_category_statistics=ec_av_category_stats)
    if cfd_av_category_stats:
        MiscImporter().import_average_cfd_category_stats(av_category_statistics=cfd_av_category_stats)
