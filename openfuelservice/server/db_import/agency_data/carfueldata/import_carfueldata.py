import hashlib
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from tqdm import tqdm

from openfuelservice.server import db
from openfuelservice.server.db_import.agency_data.carfueldata.objects import CarFuelDataCarObject
from openfuelservice.server.db_import.models import CarfuelDataCarModel
from openfuelservice.server.utils.misc.mappings import DataMappings


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


class CarFuelDataImporter:
    def __init__(self):
        self.cfd_model_objects = []

    def update_cfs_hashes(self, cfd_car_object: CarfuelDataCarModel):
        hash_id = cfd_car_object.hash_id
        db_object: CarfuelDataCarModel = db.session.query(CarfuelDataCarModel).get(hash_id)
        db_object.upate(cfd_car_object)
        db.session.commit()

    def store_cfd(self, cfd_car_object: CarFuelDataCarObject):
        manufacturer = cfd_car_object.manufacturer
        model = cfd_car_object.model
        description = cfd_car_object.description
        transmission = cfd_car_object.transmission
        engine_capacity = cfd_car_object.engine_capacity
        fuel_type = cfd_car_object.fuel_type
        real_fuel_type = DataMappings().get_fuel_type(fuel_type_to_check=fuel_type)
        date_of_change: datetime = cfd_car_object.date_of_change
        self.cfd_model_objects.append(CarfuelDataCarModel(
            hash_id=hashlib.md5((str(manufacturer).strip() +
                                 str(model).strip() +
                                 str(description).strip() +
                                 str(transmission).strip() +
                                 str(engine_capacity).strip() +
                                 str(fuel_type).strip() + date_of_change.__str__().strip()
                                 ).encode(encoding='UTF-8', errors='ignore')).hexdigest(),
            manufacturer=manufacturer,
            model=model,
            description=description,
            transmission=transmission,
            engine_capacity=engine_capacity,
            fuel_type=real_fuel_type if real_fuel_type is not False else fuel_type,
            wiki_hashes=cfd_car_object.wiki_hashes,
            e_consumption_miles_per_kWh=cfd_car_object.e_consumption_miles_per_kWh if type(
                cfd_car_object.e_consumption_miles_per_kWh) is float else None,
            e_consumption_wh_per_km=cfd_car_object.e_consumption_wh_per_km if type(
                cfd_car_object.e_consumption_wh_per_km) is float else None,
            maximum_range_km=cfd_car_object.maximum_range_km if type(
                cfd_car_object.maximum_range_km) is float else None,
            maximum_range_miles=cfd_car_object.maximum_range_miles if type(
                cfd_car_object.maximum_range_miles) is float else None,
            metric_urban_cold=cfd_car_object.metric_urban_cold if type(
                cfd_car_object.metric_urban_cold) is float else None,
            metric_extra_urban=cfd_car_object.metric_extra_urban if type(
                cfd_car_object.metric_extra_urban) is float else None,
            metric_combined=cfd_car_object.metric_combined if type(cfd_car_object.metric_combined) is float else None,
            imperial_urban_cold=cfd_car_object.imperial_urban_cold if type(
                cfd_car_object.imperial_urban_cold) is float else None,
            imperial_extra_urban=cfd_car_object.imperial_extra_urban if type(
                cfd_car_object.imperial_extra_urban) is float else None,
            imperial_combined=cfd_car_object.imperial_combined if type(
                cfd_car_object.imperial_combined) is float else None,
            co2_g_per_km=cfd_car_object.co2_g_per_km if type(cfd_car_object.co2_g_per_km) is float else None,
            fuel_cost_6000_miles=cfd_car_object.fuel_cost_6000_miles if type(
                cfd_car_object.fuel_cost_6000_miles) is float else None,
            fuel_cost_12000_miles=cfd_car_object.fuel_cost_12000_miles if type(
                cfd_car_object.fuel_cost_12000_miles) is float else None,
            electricity_cost=cfd_car_object.electricity_cost if type(
                cfd_car_object.electricity_cost) is float else None,
            total_cost_per_12000_miles=cfd_car_object.total_cost_per_12000_miles if type(
                cfd_car_object.total_cost_per_12000_miles) is float else None,
            euro_standard=cfd_car_object.euro_standard if type(cfd_car_object.euro_standard) is float else None,
            noise_level_dB_a_=cfd_car_object.noise_level_dB_a_ if type(
                cfd_car_object.noise_level_dB_a_) is float else None,
            emissions_co_mg_per_km=cfd_car_object.emissions_co_mg_per_km if type(
                cfd_car_object.emissions_co_mg_per_km) is float else None,
            thc_emissions_mg_per_km=cfd_car_object.thc_emissions_mg_per_km if type(
                cfd_car_object.thc_emissions_mg_per_km) is float else None,
            emissions_nox_mg_per_km=cfd_car_object.emissions_nox_mg_per_km if type(
                cfd_car_object.emissions_nox_mg_per_km) is float else None,
            thc_plus_nox_emissions_mg_per_km=cfd_car_object.thc_plus_nox_emissions_mg_per_km if type(
                cfd_car_object.thc_plus_nox_emissions_mg_per_km) is float else None,
            particulates_no_mg_per_km=cfd_car_object.particulates_no_mg_per_km if type(
                cfd_car_object.particulates_no_mg_per_km) is float else None,
            rde_nox_urban=cfd_car_object.rde_nox_urban if type(cfd_car_object.rde_nox_urban) is float else None,
            rde_nox_combined=cfd_car_object.rde_nox_combined if type(
                cfd_car_object.rde_nox_combined) is float else None,
            date_of_change=date_of_change if type(date_of_change) is datetime else None,
            year=cfd_car_object.year
        ))
        if len(self.cfd_model_objects) >= 400:
            fallback_importer(self.cfd_model_objects)
            self.cfd_model_objects = []

    def import_cfd(self, cfd_data: []):
        for cfd_car_object in tqdm(cfd_data, total=len(cfd_data), unit=' Importing CarFuelData'):
            if type(cfd_car_object) == CarFuelDataCarObject:
                self.store_cfd(cfd_car_object)
            elif type(cfd_car_object) == CarfuelDataCarModel:
                self.cfd_model_objects.append(cfd_car_object)
        fallback_importer(self.cfd_model_objects)
