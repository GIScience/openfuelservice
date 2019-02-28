import time

import schedule

from openfuelservice.server import ofs_settings, temp_folder, create_app
from openfuelservice.server.db_import import parser
from openfuelservice.server.drivers import countries_driver
from openfuelservice.server.drivers.envirocar_driver import ECData
from openfuelservice.server.drivers.eurostat_driver import ESData
from openfuelservice.server.utils.database.database_tools import compare_with_hashtable
from openfuelservice.server.utils.misc import file_management
from openfuelservice.server.utils.misc.file_management import download_file

eurostat_settings = ofs_settings['statistics_provider']['eurostat_oil_provider']
oil_history_2005_url = eurostat_settings['oil_history_2005']['url']


def eurostat_update():
    app = create_app()
    app.app_context().push()
    file_management.create_directory(temp_folder)
    file_management.clean_directory(temp_folder)
    history_2005 = download_file(oil_history_2005_url)
    if history_2005 is not None:
        # Update 2005 fuel history
        compare_result = compare_with_hashtable(history_2005)
        if compare_result:
            print("Eurostat prices after 2005 up to date")
            pass
        else:
            print("Updating Eurostat prices after 2005")
            country_codes = countries_driver.CountryData().get()
            history2005 = ESData(history2005=True).get(country_codes=country_codes)
            parser.parse_eurostat(history2005)


def envirocar_update():
    app = create_app()
    app.app_context().push()
    envirocar_data = ECData(all_parameters_min=True).get()
    parser.parse_envirocar(envirocar_data=envirocar_data)


def calc_models_update():
    """
    # TODO run this as thread!
    # Calc the sensor models here.
    # Should not be called from any other function. Just runs in one thread! Once the thread calced every model it will
    # constantly check for changes in tracks or sensors! --> So it will be responsible for all statistics and measurement downloads.
    # Once downloaded all of them will be stored in the db but not crawled all at the same time.
    # It won't be callable from anywhere. It will stay in the thread. Everytime it finishes a model it will first check
    # all already calculated models for updates before starting a new one.
    # Solution for db update --> Add a collumn to the sensor models table that indicates
    # from how many (or from what tracks exactly?!?!) the model was calculated
    # If a new model is present it will be crawled after that.
    """
    # Sensor per sensor. 1. Tracks of Sensor 2. Measurements of Tracks, 3. z-coordinate adjustment 4. Calc model
    # ----------------------------------------------------------------------------------------------------------------
    # Examples!!!
    # imported_tracks = db.session.query(EnvirocarTrackModel.track_id).all()
    # imported_tracks_stats = db.session.query(EnvirocarTrackStatisticModel.track_id).all()
    # tracks_to_crawl = []
    # if len(imported_tracks) > 0:
    #     if len(imported_tracks_stats) > 0:
    #         temp = []
    #         for element in imported_tracks_stats:
    #             temp.append(element.track_id)
    #         for element in imported_tracks:
    #             if element.track_id in temp:
    #                 pass
    #             else:
    #                 tracks_to_crawl.append(element.track_id)
    #     else:
    #         for element in imported_tracks:
    #             tracks_to_crawl.append(element.track_id)
    #     parser.parse_envirocar_advanced(ECData(exc_track_statistics=True).get(track_data=tracks_to_crawl))
    # pass


def run_model_calc():
    schedule.every(60).minutes.do(calc_models_update)
    while 1:
        schedule.run_pending()
        time.sleep(1)


def run_updates():
    # Todo implement the initial Track geometry leeching here! OR already in the manage.py? It always starts at the
    #  beginning and fails if only one entry is in the database
    schedule.every(30).minutes.do(envirocar_update)
    schedule.every(3).days.do(eurostat_update)
    while 1:
        schedule.run_pending()
        time.sleep(1)
