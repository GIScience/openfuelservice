import sys
import unittest

from flask.cli import FlaskGroup

from openfuelservice.server import create_app, temp_folder, ofs_settings
from openfuelservice.server.db_import import parser
from openfuelservice.server.db_import.models import *
from openfuelservice.server.drivers.carfueldata_driver import LatestCars
from openfuelservice.server.drivers.countries_driver import CountryData
from openfuelservice.server.drivers.envirocar_driver import ECData
from openfuelservice.server.drivers.eurostat_driver import ESData
from openfuelservice.server.drivers.misc_driver import EnvirocarWikiMatcher, CarFuelDataWikiMatcher
from openfuelservice.server.drivers.wikipedia_driver import get_wikipedia_car_data, ProcessWikipediaCarTexts
from openfuelservice.server.statistics.misc_statistics import EnvirocarAverageCategoryStatistics, \
    CFDAverageCategoryStatistics
from openfuelservice.server.utils.database.database_tools import DBSetup, clear_tables
from openfuelservice.server.utils.database.queries import get_relevevant_brands
from openfuelservice.server.utils.matching.tf.create_models import ManufacturerANNModelCollection
from openfuelservice.server.utils.matching.tf.matching_assessment import AnnMatchingRefinement, FixedMatchingAssessment
from openfuelservice.server.utils.misc import file_management

app = create_app()
cli = FlaskGroup(create_app=create_app)
server_mode = ofs_settings['general']['server_mode']


@cli.command()
def test():
    """Runs the unit tests without test coverage."""
    tests = unittest.TestLoader().discover('openfuelservice/tests', pattern='test*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    return 1


@cli.command()
def create_db():
    """Drops and creates a fresh db, the standard user and the tables."""
    """Important Note: Models must be imported at least once somewhere, else Flask will not recognize them internally. 
    So in order to run db.create_all() import models at least here, even though they are not used actively.
    """
    if server_mode:
        DBSetup().create()
        db.create_all()


@cli.command()
def drop_db():
    """Drops the complete db."""
    if server_mode:
        db.drop_all()


@cli.command()
def clean_db():
    """Cleans all tables"""
    clear_tables(db=db, session=db.session)


@cli.command()
def create_ann_models():
    # Get agency data
    #  --> Use correct matches to fill the tensorflow validation samples?
    # TODO Overwork the blacklist files. --> Still necessary? Maybe better results without
    relevant_brands = get_relevevant_brands()
    for brand in relevant_brands:
        wikicar_texts = ProcessWikipediaCarTexts(filter_brand=brand).get_wikicar_texts(dummy=False)
        parser.parse_wikipedia(wikicar_texts=wikicar_texts)
        wikicar_texts.clear()
    collection = ManufacturerANNModelCollection()
    collection.load_models()
    collection.create_models(manufacturers=relevant_brands, wiki_pages=True, manual_intents=False,
                             intent_cars_only=False)


def ann_model_assessment():
    # Brand by brand!
    # 1. Get live matches
    # 2. Get live missings
    # 3. Lead through manual assessment
    # 3.1 For missing add related Wiki Name --> Create Powerset from missing name --> Manual intents
    # 3.2 For wrong matches add correct wiki name --> Create Powerset --> Manual intents
    # 3.3 For right matches --> Create Powerset --> Manual intents
    # 3.4 Store processed matches in
    # 4. Store to manual intents
    assessment = AnnMatchingRefinement(envirocar=True, carfueldata=True)
    assessment.assess_missing_cars()
    assessment.assess_matched_cars()


@cli.command()
def fixed_matching_assessment():
    FixedMatchingAssessment(envirocar=True, carfueldata=False, matchedData=False).assess()
    pass


@cli.command()
def match_data():
    # Match wikipedia car data and envirocar
    matched_envirocar_data = EnvirocarWikiMatcher().match(matching_score=0.99998, complex_matching=False)
    parser.parse_envirocar(envirocar_data=matched_envirocar_data)
    # TODO change matching score to 1 and leave the complex and unconditional matching to fuzzy matching?
    matched_cfd_data = CarFuelDataWikiMatcher().match(matching_score=0.96, complex_matching=True)
    parser.parse_cfd(matched_cfd_data)

    # Generate Average Statistics
    ec_ev_statistics = EnvirocarAverageCategoryStatistics().calculate()
    parser.parse_misc(ec_av_category_stats=ec_ev_statistics)
    cfd_ev_statistics = CFDAverageCategoryStatistics().calculate()
    parser.parse_misc(cfd_av_category_stats=cfd_ev_statistics)


@cli.command()
def calculate_av_data():
    # Generate Average Statistics
    ec_ev_statistics = EnvirocarAverageCategoryStatistics().calculate()
    parser.parse_misc(ec_av_category_stats=ec_ev_statistics)
    cfd_ev_statistics = CFDAverageCategoryStatistics().calculate()
    parser.parse_misc(cfd_av_category_stats=cfd_ev_statistics)


@cli.command()
def import_data():
    """Runs the initial data importer"""
    if server_mode:
        file_management.create_directory(temp_folder)
        file_management.clean_directory(temp_folder)

        clear_tables(db=db, session=db.session)

        country_codes = CountryData().get()
        parser.parse_countries(country_codes)

        # Crawl and parse Eurostat
        eurostat_data = ESData(all_parameters=True).get(country_codes=country_codes)
        parser.parse_eurostat(eurostat_data=eurostat_data)

        # Crawl Wikipedia data
        car_categories, car_objects = get_wikipedia_car_data()
        parser.parse_wikipedia(wikicar_categories=car_categories, wikicar_objects=car_objects)

        # Crawl Envirocar data
        envirocar_data = ECData(all_parameters_min=True).get_data()
        parser.parse_envirocar(envirocar_data=envirocar_data)

        # Get CFD data
        latest_carfueldata_cars = LatestCars().get_data()
        parser.parse_cfd(cfd_data=latest_carfueldata_cars)

        # Clean the temp folder
        file_management.clean_directory(temp_folder)
    else:
        print("Couldn't run database import. Flask server started in client only mode!")


if __name__ == '__main__':
    # Escape the tasks if the run parameter is not set. Else flask will never finish in other (dev, test etc.)
    args = sys.argv[1:]
    if len(args) != 1:
        print("One argument is allowed and necessary to pass to the server. You passed {} arguments!".format(len(args)))
        raise ValueError(Exception)
    elif sys.argv[1] == "run" and server_mode:
        pass
        # t = Thread(target=run_updates)
        # t2 = Thread(target=run_model_calc)
        # t.start()
        # t2.start()
    cli()
