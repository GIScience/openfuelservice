import hashlib

from sqlalchemy.exc import IntegrityError
from tqdm import tqdm

from openfuelservice.server import db
from openfuelservice.server.db_import.eurostat.objects import CountryPrice, GeneralPrice
from openfuelservice.server.db_import.models import EurostatGeneralPriceModel, EurostatCountryPriceModel


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


class EurostatImporter:

    def __init__(self):
        # Temp variable to verify the data
        self.countries = []
        self.country_price_objects = []
        self.general_price_objects = []

    def create_country_price(self, country_alpha_2, date, country_prices):
        taux = country_prices['taux']
        euro_price = country_prices['euro_price']
        euro_unit = country_prices['euro_unit']
        euro_quantity = country_prices['euro_quantity']
        diesel_unit = country_prices['diesel_unit']
        diesel_quantity = country_prices['diesel_quantity']

        euro_ht = 0.0
        if 'euro_ht' in country_prices and type(country_prices['euro_ht']) is not str:
            euro_ht = country_prices['euro_ht']

        euro_ttc = 0.0
        if 'euro_ttc' in country_prices and country_prices['euro_ttc'] is not None and \
                type(country_prices['euro_ttc']) is not str:
            euro_ttc = country_prices['euro_ttc']

        diesel_ht = 0.0
        if 'diesel_ht' in country_prices and country_prices['diesel_ht'] is not None and \
                type(country_prices['diesel_ht']) is not str:
            diesel_ht = country_prices['diesel_ht']

        diesel_ttc = 0.0
        if 'diesel_ttc' in country_prices and country_prices['diesel_ttc'] is not None and \
                type(country_prices['diesel_ttc']) is not str:
            diesel_ttc = country_prices['diesel_ttc']

        self.store_country_price_object(CountryPrice(
            date=date,
            country_alpha_2=country_alpha_2,
            taux=taux,
            euro_price=euro_price,
            euro_ht=euro_ht,
            euro_ttc=euro_ttc,
            euro_unit=euro_unit,
            euro_quantity=euro_quantity,
            diesel_ht=diesel_ht,
            diesel_ttc=diesel_ttc,
            diesel_unit=diesel_unit,
            diesel_quantity=diesel_quantity
        ))

    def store_country_price_object(self, price_object):
        self.country_price_objects.append(EurostatCountryPriceModel(
            hash_id=hashlib.md5(
                (str(price_object.date).strip() + str(price_object.country_alpha_2).strip()).encode(encoding='UTF-8',
                                                                                                    errors='ignore')).hexdigest(),
            date=price_object.date,
            country_alpha_2=price_object.country_alpha_2,
            taux=price_object.taux,
            euro_price=price_object.euro_price,
            euro_ht=price_object.euro_ht,
            euro_ttc=price_object.euro_ttc,
            euro_unit=price_object.euro_unit,
            euro_quantity=price_object.euro_quantity,
            diesel_ht=price_object.diesel_ht,
            diesel_ttc=price_object.diesel_ttc,
            diesel_unit=price_object.diesel_unit,
            diesel_quantity=price_object.diesel_quantity
        ))

    def create_general_price(self, date, general_price):
        euro_price = general_price['euro_price']
        euro_unit = general_price['euro_unit']
        euro_quantity = general_price['euro_quantity']
        euro_ht = general_price['euro_ht'] if 'euro_ht' in general_price else None
        diesel_unit = general_price['diesel_unit']
        diesel_quantity = general_price['diesel_quantity']
        if euro_ht is None or type(euro_ht) is str:
            euro_ht = 0.0

        euro_ttc = general_price['euro_ttc'] if 'euro_ttc' in general_price else None
        if euro_ttc is None or type(euro_ttc) is str:
            euro_ttc = 0.0

        diesel_ht = general_price['diesel_ht'] if 'diesel_ht' in general_price else None
        if diesel_ht is None or type(diesel_ht) is str:
            diesel_ht = 0.0

        diesel_ttc = general_price['diesel_ttc'] if 'diesel_ttc' in general_price else None
        if diesel_ttc is None or type(diesel_ttc) is str:
            diesel_ttc = 0.0
        self.store_general_price_object(GeneralPrice(
            date=date,
            euro_price=euro_price,
            euro_ht=euro_ht,
            euro_ttc=euro_ttc,
            euro_unit=euro_unit,
            euro_quantity=euro_quantity,
            diesel_ht=diesel_ht,
            diesel_ttc=diesel_ttc,
            diesel_unit=diesel_unit,
            diesel_quantity=diesel_quantity
        ))

    def store_general_price_object(self, general_price_object):
        self.general_price_objects.append(EurostatGeneralPriceModel(
            hash_id=hashlib.md5(
                (str(general_price_object.date).strip()).encode(encoding='UTF-8', errors='ignore')).hexdigest(),
            date=general_price_object.date,
            euro_price=general_price_object.euro_price,
            euro_ht=general_price_object.euro_ht,
            euro_ttc=general_price_object.euro_ttc,
            euro_unit=general_price_object.euro_unit,
            euro_quantity=general_price_object.euro_quantity,
            diesel_ht=general_price_object.diesel_ht,
            diesel_ttc=general_price_object.diesel_ttc,
            diesel_unit=general_price_object.diesel_unit,
            diesel_quantity=general_price_object.diesel_quantity
        ))

    def import_countries(self, country_prices):
        # TODO finish update feature
        if db.session.query(EurostatCountryPriceModel).first() is not None:
            dates = dict()
            db_entries = db.session.query(EurostatCountryPriceModel.date,
                                          EurostatCountryPriceModel.country_alpha_2).all()
            for entry in db_entries:
                if entry.country_alpha_2 not in dates:
                    dates[entry.country_alpha_2] = []
                dates[entry.country_alpha_2].append(entry.date.date())
            for country in tqdm(country_prices, total=len(country_prices), unit=' Updating Country Fuel Prices'):
                for date in country_prices[country]:
                    if country in dates and date in dates[country]:
                        pass
                    else:
                        self.create_country_price(country, date, country_prices[country][date])
                fallback_importer(self.country_price_objects)
                self.country_price_objects.clear()
        else:
            for country in tqdm(country_prices, total=len(country_prices), unit=' Importing Country Fuel Prices'):
                for date in country_prices[country]:
                    self.create_country_price(country, date, country_prices[country][date])
                fallback_importer(self.country_price_objects)
                self.country_price_objects.clear()
        pass

    def import_general(self, general_prices):
        if db.session.query(EurostatGeneralPriceModel).first() is not None:
            db_entries = db.session.query(EurostatGeneralPriceModel.date).all()
            dates = []
            for entry in db_entries:
                dates.append(entry.date.date())
            for date in tqdm(general_prices, total=len(general_prices), unit=' Updating General Fuel Prices'):
                if date in dates:
                    pass
                else:
                    self.create_general_price(date, general_prices[date])
            fallback_importer(self.general_price_objects)
            self.general_price_objects.clear()
        else:
            for date in tqdm(general_prices, total=len(general_prices), unit=' Importing General Fuel Prices'):
                self.create_general_price(date, general_prices[date])
            fallback_importer(self.general_price_objects)
            self.general_price_objects.clear()

