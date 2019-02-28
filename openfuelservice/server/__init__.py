import logging
import os
import time
from pathlib import Path

import yaml
from flasgger import Swagger
from flask import Flask, g, jsonify
from flask_bootstrap import Bootstrap
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from openfuelservice.server.api import api_exceptions

logger = logging.getLogger(__name__)

"""load custom settings for openfuelservice and add important path's"""
# Basic variables
basedir = Path(__file__).parent
ofs_settings = yaml.safe_load(open(basedir.joinpath('ofs_settings.yml').as_posix(), encoding='utf-8'))
temp_folder = basedir.joinpath(ofs_settings['general']['temporary_folder'])
file_folder = basedir.joinpath(ofs_settings['general']['file_folder'])

# Categories and matching variables
category_list = yaml.safe_load(
    open(basedir.joinpath('categories').joinpath('categories.yml').as_posix(), encoding='utf-8'))
car_brands = yaml.safe_load(
    open(basedir.joinpath('categories').joinpath('car_brands.yml').as_posix(), encoding='utf-8'))
fixed_matches = yaml.safe_load(
    open(basedir.joinpath('categories').joinpath('fixed_matches.yml').as_posix(), encoding='utf-8'))
ann_settings = ofs_settings['ann_settings']
ignore_list = ofs_settings['general']['advanced_settings']['ignore_list']
verbose = ofs_settings['general']['verbose']
allowed_fuel_types = ofs_settings['general']['enabled_fuel_types']

# Attributions
carfueldata_attribution = ofs_settings['statistics_provider']['carfueldata_provider']['attribution']
envirocar_attribution = ofs_settings['statistics_provider']['envirocar_provider']['attribution']
eurostat_attribution = ofs_settings['statistics_provider']['eurostat_oil_provider']['attribution']

# Credentials
pg_settings = ofs_settings['provider_parameters']
admin = pg_settings['admin_user']
admin_pw = pg_settings['admin_password']
super_admin = pg_settings['super_admin']
super_admin_pw = pg_settings['su_password']
database = pg_settings['db_name']

# Tables
ec_tables = ofs_settings['statistics_provider']['envirocar_provider']['table_names']
ec_geom = ofs_settings['statistics_provider']['envirocar_provider']['geometry_column']
es_tables = ofs_settings['statistics_provider']['eurostat_oil_provider']['table_names']
misc_tables = ofs_settings['statistics_provider']['misc']['table_names']
wiki_car_table = ofs_settings['general']['wikipedia_car_table']
wiki_category_table = ofs_settings['general']['wikipedia_category_table']
cfd_tables = ofs_settings['statistics_provider']['carfueldata_provider']['table_names']
countries_table = ofs_settings['general']['countries_table']
hash_table = ofs_settings['general']['hash_table']

# if "TESTING" in os.environ:
#     ec_tables_testing = list()
#     es_tables_testing = list()
#     misc_tables_testing = list()
#     cfd_tables_testing = list()
#     for table in ec_tables:
#         ec_tables_testing.append(table + '_test')
#     for table in es_tables:
#         es_tables_testing.append(table + '_test')
#     for table in misc_tables:
#         misc_tables_testing.append(table + '_test')
#     for table in cfd_tables:
#         cfd_tables_testing.append(table + '_test')
#     ec_tables = ec_tables_testing
#     es_tables = es_tables_testing
#     misc_tables = misc_tables_testing
#     cfd_tables = cfd_tables_testing

db = SQLAlchemy(session_options={'autocommit': False, 'autoflush': False})


def create_app(script_info=None):
    # instantiate the app

    app = Flask(__name__)
    cors = CORS(app, resources={r"/fuel*": {"origins": "*"}})
    app.config['SWAGGER'] = {
        'title': 'Openfuelservice',
        "swagger_version": "2.0",
        'version': 0.1,
        'uiversion': 3
    }
    # set config

    # TODO Add a if clause later to add read and read/write behaviour
    app_settings = os.getenv('APP_SETTINGS', 'openfuelservice.server.config.ProductionConfig')
    app.config.from_object(app_settings)
    # set up extensions
    db.init_app(app)

    Bootstrap(app)

    # register blueprints
    from openfuelservice.server.api.views import main_blueprint
    app.register_blueprint(main_blueprint)

    Swagger(app, template_file='api/ofs_post.yml')

    if "DEVELOPMENT" in os.environ:
        @app.before_request
        def before_request():
            g.start = time.time()

        @app.teardown_request
        def teardown_request(exception=None):
            # if 'start' in g:
            diff = time.time() - g.start
            logger.info("Request took: {} seconds".format(diff))

    # error handlers
    @app.errorhandler(401)
    def unauthorized_page(error):
        return jsonify({"error_message": 401})

    @app.errorhandler(403)
    def forbidden_page(error):
        return jsonify({"error_message": 403})

    @app.errorhandler(404)
    def page_not_found(error):
        return jsonify({"error_message": 404})

    @app.errorhandler(500)
    def server_error_page(error):
        return jsonify({"error_message": 500})

    @app.errorhandler(api_exceptions.InvalidUsage)
    def handle_invalid_usage(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    # shell context for flask cli
    app.shell_context_processor({
        'app': app,
        'db': db}
    )
    return app
