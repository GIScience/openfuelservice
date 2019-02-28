from shapely.geometry import shape, MultiPolygon
from sqlalchemy.exc import IntegrityError
from tqdm import tqdm

from openfuelservice.server import db
from openfuelservice.server.db_import.countries.objects import CountryObject
from openfuelservice.server.db_import.models import CountryDataModel


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


class CountryImporter:
    def __init__(self):
        self.country_objects = []

    def create_country(self, country_name, country_data):
        iso2 = country_data['ISO3166-1-Alpha-2']
        iso3 = country_data['ISO3166-1-Alpha-3']
        numeric = country_data['ISO3166-1-numeric']
        curr_code = country_data['ISO4217-currency_alphabetic_code']
        curr_name = country_data['ISO4217-currency_name']
        geom = country_data['geom']
        if geom['type'] == 'Polygon':
            geom_wkt = shape(MultiPolygon([shape(geom)]))
        else:
            geom_wkt = shape(geom)
        country_obj = CountryObject(
            country_name=country_name,
            country_alpha_2=iso2,
            country_alpha_3=iso3,
            country_numeric=numeric,
            country_currency_code=curr_code,
            country_currency_name=curr_name,
            geom=geom_wkt)
        self.store_country(country_obj)

    def store_country(self, country_obj):
        # object_temp = CountryDataModel.query.order_by(CountryDataModel.country_name).all()
        self.country_objects.append(CountryDataModel(
            country_name=country_obj.country_name,
            country_alpha_2=country_obj.country_alpha_2,
            country_alpha_3=country_obj.country_alpha_3,
            country_numeric=country_obj.country_numeric,
            country_currency_code=country_obj.country_currency_code,
            country_currency_name=country_obj.country_currency_name,
            geom=country_obj.geom
        ))

    def import_countries(self, countries):
        for country in tqdm(countries, total=len(countries), unit=' Importing Countries'):
            self.create_country(country, countries[country])
        fallback_importer(self.country_objects)
        self.country_objects = []
        pass
