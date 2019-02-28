from geoalchemy2.shape import from_shape
from shapely.geometry import Point, LineString
from sqlalchemy import desc, or_, and_, asc

from openfuelservice.server import db
from openfuelservice.server.db_import.eurostat.objects import CountryPrice, GeneralPrice, CountryPriceExtended
from openfuelservice.server.db_import.models import CountryDataModel, EurostatCountryPriceModel, \
    EurostatGeneralPriceModel, \
    EnvirocarAverageCategoryStatisticsModel, \
    EnvirocarPhenomenonModel, CarCategoryModel, CarFuelDataAverageCategoryStatisticsModel, CarfuelDataCarModel


def query_country_price_by_linestring(linestring: LineString):
    wkt_element = from_shape(shape=linestring, srid=4326)
    query = (
        db.session.query(CountryDataModel.country_alpha_2, CountryDataModel.geom, EurostatCountryPriceModel.date,
                         EurostatCountryPriceModel.diesel_quantity,
                         EurostatCountryPriceModel.diesel_unit, EurostatCountryPriceModel.diesel_ttc,
                         EurostatCountryPriceModel.diesel_ht,
                         EurostatCountryPriceModel.euro_quantity,
                         EurostatCountryPriceModel.euro_unit, EurostatCountryPriceModel.euro_ttc,
                         EurostatCountryPriceModel.euro_ht,
                         EurostatCountryPriceModel.taux).filter(
            CountryDataModel.geom.ST_Intersects(wkt_element)).join(
            EurostatCountryPriceModel,
            CountryDataModel.country_alpha_2 == EurostatCountryPriceModel.country_alpha_2).order_by(
            desc(EurostatCountryPriceModel.date)).all())
    country_check = []
    cpo_extended_return = []
    for result in query:
        country = result.country_alpha_2
        if country not in country_check:
            country_check.append(country)
            cpo_extended_return.append(CountryPriceExtended(
                date=result.date,
                country_alpha_2=result.country_alpha_2,
                euro_ttc=result.euro_ttc / result.euro_quantity,
                diesel_ttc=result.diesel_ttc / result.diesel_quantity,
                euro_unit=result.euro_unit,
                euro_quantity=result.euro_quantity / result.euro_quantity,
                diesel_unit=result.diesel_unit,
                diesel_quantity=result.diesel_quantity / result.diesel_quantity,
                euro_price=1,
                taux=result.taux,
                diesel_ht=result.diesel_ht / result.diesel_quantity,
                euro_ht=result.euro_ht / result.euro_quantity,
                geom=result.geom
            ))
    return cpo_extended_return


def query_country_price_by_point(point: Point) -> CountryPrice:
    wkt_element = from_shape(point, srid=4326)
    query = (
        db.session.query(CountryDataModel.country_alpha_2,
                         EurostatCountryPriceModel.date,
                         EurostatCountryPriceModel.diesel_quantity,
                         EurostatCountryPriceModel.diesel_unit,
                         EurostatCountryPriceModel.diesel_ttc,
                         EurostatCountryPriceModel.diesel_ht,
                         EurostatCountryPriceModel.euro_quantity,
                         EurostatCountryPriceModel.euro_unit,
                         EurostatCountryPriceModel.euro_ttc,
                         EurostatCountryPriceModel.euro_ht,
                         EurostatCountryPriceModel.taux).filter(
            CountryDataModel.geom.ST_Intersects(wkt_element)).join(
            EurostatCountryPriceModel,
            CountryDataModel.country_alpha_2 == EurostatCountryPriceModel.country_alpha_2).order_by(
            desc(EurostatCountryPriceModel.date)).first())
    cpo = CountryPrice(
        date=query.date,
        country_alpha_2=query.country_alpha_2,
        euro_ttc=query.euro_ttc / query.euro_quantity,
        diesel_ttc=query.diesel_ttc / query.diesel_quantity,
        euro_unit=query.euro_unit,
        euro_quantity=query.euro_quantity / query.euro_quantity,
        diesel_unit=query.diesel_unit,
        diesel_quantity=query.diesel_quantity / query.diesel_quantity,
        euro_price=1,
        taux=query.taux,
        diesel_ht=query.diesel_ht / query.diesel_quantity,
        euro_ht=query.euro_ht / query.euro_quantity
    )
    return cpo


def query_countries():
    query = (db.session.query(CountryDataModel.country_alpha_2,
                              CountryDataModel.country_name).all())
    return query


def query_countries_w_prices():
    all_countries = query_countries()
    countries_w_prices = dict()
    for country in all_countries:
        if country.country_alpha_2 not in countries_w_prices:
            country_name = country.country_alpha_2
            price = query_oldest_country_price(country_name)
            if price is not None:
                countries_w_prices[country_name] = price.date.year
    return countries_w_prices


def query_oldest_country_price(country):
    query = (db.session.query(CountryDataModel.country_alpha_2,
                              EurostatCountryPriceModel.date).filter(
        CountryDataModel.country_alpha_2 == country).join(
        EurostatCountryPriceModel,
        CountryDataModel.country_alpha_2 == EurostatCountryPriceModel.country_alpha_2).order_by(
        asc(EurostatCountryPriceModel.date)).first())
    return query


def query_general_price() -> GeneralPrice:
    query = (
        db.session.query(EurostatGeneralPriceModel.date, EurostatGeneralPriceModel.euro_ttc,
                         EurostatGeneralPriceModel.euro_ht,
                         EurostatGeneralPriceModel.euro_unit,
                         EurostatGeneralPriceModel.euro_quantity,
                         EurostatGeneralPriceModel.diesel_ttc, EurostatGeneralPriceModel.diesel_ht,
                         EurostatGeneralPriceModel.diesel_unit,
                         EurostatGeneralPriceModel.diesel_quantity).order_by(
            desc(EurostatGeneralPriceModel.date)).first())
    gpo = GeneralPrice(
        date=query.date,
        euro_ttc=query.euro_ttc / query.euro_quantity,
        diesel_ttc=query.diesel_ttc / query.diesel_quantity,
        euro_unit=query.euro_unit,
        euro_quantity=query.euro_quantity / query.euro_quantity,
        diesel_unit=query.diesel_unit,
        diesel_quantity=query.diesel_quantity / query.diesel_quantity,
        euro_price=1,
        diesel_ht=query.diesel_ht / query.diesel_quantity,
        euro_ht=query.euro_ht / query.euro_quantity
    )
    return gpo


def query_ec_average_category_statistics(fuel_type: str) -> list:
    query: list = (
        db.session.query(EnvirocarAverageCategoryStatisticsModel).filter(
            or_(EnvirocarPhenomenonModel.name == 'CO2', EnvirocarPhenomenonModel.name == 'Consumption',
                EnvirocarPhenomenonModel.name == 'Speed'),
            and_(EnvirocarAverageCategoryStatisticsModel.fuel_type == fuel_type)).join(
            EnvirocarPhenomenonModel,
            EnvirocarPhenomenonModel.name == EnvirocarAverageCategoryStatisticsModel.phenomenon_name).all())
    return query


def query_cfd_average_category_statistics(fuel_type: str) -> list:
    query: list = (
        db.session.query(CarFuelDataAverageCategoryStatisticsModel).filter(
            CarFuelDataAverageCategoryStatisticsModel.fuel_type == fuel_type).all())
    return query


def query_cfd_model(cfd_id: str):
    query: list = (
        db.session.query(CarfuelDataCarModel).filter(
            CarfuelDataCarModel.hash_id == cfd_id).first())
    return query

def query_cfd_category(fuel_type: str, category: str) -> list:
    query: list = (
        db.session.query(CarFuelDataAverageCategoryStatisticsModel).filter(
            or_(CarFuelDataAverageCategoryStatisticsModel.phenomenon_name == 'co2_g_per_km',
                CarFuelDataAverageCategoryStatisticsModel.phenomenon_name == 'metric_combined',
                CarFuelDataAverageCategoryStatisticsModel.phenomenon_name == 'metric_extra_urban',
                CarFuelDataAverageCategoryStatisticsModel.phenomenon_name == 'metric_urban_cold',
                CarFuelDataAverageCategoryStatisticsModel.phenomenon_name == 'emissions_co_mg_per_km',
                CarFuelDataAverageCategoryStatisticsModel.phenomenon_name == 'emissions_nox_mg_per_km',
                CarFuelDataAverageCategoryStatisticsModel.phenomenon_name == 'thc_emissions_mg_per_km',
                CarFuelDataAverageCategoryStatisticsModel.phenomenon_name == 'thc_plus_nox_emissions_mg_per_km',
                CarFuelDataAverageCategoryStatisticsModel.phenomenon_name == 'noise_level_dB_a_'),
            and_(CarFuelDataAverageCategoryStatisticsModel.fuel_type == fuel_type,
                 CarFuelDataAverageCategoryStatisticsModel.category_short_eu == category)).all())
    return query


def query_ec_category(fuel_type: str, category: str) -> list:
    query: list = (
        db.session.query(EnvirocarAverageCategoryStatisticsModel).filter(
            or_(EnvirocarPhenomenonModel.name == 'CO2', EnvirocarPhenomenonModel.name == 'Consumption',
                EnvirocarPhenomenonModel.name == 'Speed'),
            and_(EnvirocarAverageCategoryStatisticsModel.fuel_type == fuel_type)).join(
            EnvirocarPhenomenonModel,
            EnvirocarPhenomenonModel.name == EnvirocarAverageCategoryStatisticsModel.phenomenon_name).all())

    query: list = (
        db.session.query(EnvirocarAverageCategoryStatisticsModel).filter(
            or_(EnvirocarPhenomenonModel.name == 'CO2', EnvirocarPhenomenonModel.name == 'Consumption',
                EnvirocarPhenomenonModel.name == 'Speed'),
            and_(EnvirocarAverageCategoryStatisticsModel.fuel_type == fuel_type),
            and_(EnvirocarAverageCategoryStatisticsModel.category_short_eu == category)).join(
            EnvirocarPhenomenonModel,
            EnvirocarPhenomenonModel.name == EnvirocarAverageCategoryStatisticsModel.phenomenon_name).all())
    return query


def query_category_for_category_short(category_short_eu: str) -> CarCategoryModel:
    query: CarCategoryModel or None = (
        db.session.query(CarCategoryModel).filter(CarCategoryModel.category_short_eu == category_short_eu).first())
    return query


