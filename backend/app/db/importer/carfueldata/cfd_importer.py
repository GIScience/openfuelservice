from typing import List

from sqlalchemy.orm import Session
from tqdm import tqdm

from app.db.importer.base_importer import BaseImporter
from app.db.importer.carfueldata.cfd_objects import CFDImportCar
from app.db.importer.carfueldata.cfd_reader import CarFuelDataReader
from app.models import CarFuelDataCar


class CarFuelDataImporter(BaseImporter):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cfd_model_objects: List = []

    # def update_cfs_hashes(self, cfd_car_object: CarFuelDataCar) -> None:
    #     hash_id = cfd_car_object.id
    #     db_object: CarFuelDataCar = self.db.query(CarFuelDataCar).get(hash_id)
    #     db_object.update(cfd_car_object)
    #     self.db.commit()

    def _store_cfd(self, cfd_car_import: CFDImportCar) -> None:
        cfd_db_car: CarFuelDataCar = CarFuelDataCar()
        cfd_db_car.translate_import(cfd_import_car=cfd_car_import)
        self.cfd_model_objects.append(cfd_db_car)

    def import_cfd_reader(self, cfd_reader: CarFuelDataReader) -> None:
        for cfd_car_object in tqdm(
            cfd_reader.cfd_objects_list,
            total=len(cfd_reader.cfd_objects_list),
            unit=" Importing CarFuelData",
        ):
            if type(cfd_car_object) == CFDImportCar:
                self._store_cfd(cfd_car_object)
            elif type(cfd_car_object) == CarFuelDataCar:
                self.cfd_model_objects.append(cfd_car_object)
        self.fallback_importer(self.cfd_model_objects)
