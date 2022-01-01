import logging
from typing import Dict, List, Union

from sqlalchemy import exc
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import FlushError
from tqdm import tqdm

from app.db.importer.carfueldata.cfd_reader import CarFuelDataReader
from app.models import CarFuelDataCar

logger = logging.getLogger(__name__)


class BaseImporter:
    def __init__(self, db: Session):
        self.db: Session = db
        self._int_hashes: Dict = {}
        self._object_collection: List = []

    def import_data(self, reader_object: Union[CarFuelDataReader]) -> None:
        for cfd_car_object in tqdm(
            reader_object.objects_list,
            total=len(reader_object.objects_list),
            unit=f"Importing Database Objects for class {self.__class__}",
        ):
            if type(cfd_car_object) == CarFuelDataCar:
                self._object_collection.append(cfd_car_object)
        self._fallback_importer()

    def _fallback_importer(self, merge_on_duplicate: bool = True) -> None:
        """
        Working as the general importer with a duplicate key check build in. If a duplicate exists it is removed from
        the collection. If a key exists in the database the entry is merged, if set to true.

        :param merge_on_duplicate: Set to ture to merge existing database objects.
        """
        counter = 0
        db_object_hashes: set = set()
        for i in range(len(self._object_collection) - 1, -1, -1):
            db_object: CarFuelDataCar = self._object_collection[i]
            if db_object.id not in db_object_hashes:
                db_object_hashes.add(db_object.id)
            else:
                self._object_collection.pop(i)
                counter += 1
                continue
            if merge_on_duplicate and self._object_collection[i].get_all_by_filter(
                self.db, [self._object_collection[i].id]
            ):
                self.db.merge(self._object_collection.pop(i))

        try:
            self.db.add_all(self._object_collection)
            self.db.commit()
        except exc.IntegrityError as err:
            logger.warning(f"Integrity error with message: {err}")
            self.db.rollback()
        except TypeError as err:
            logger.warning(f"Type error with message: {err}")
            self.db.rollback()
        except FlushError as err:
            logger.warning(f"Flush error with message: {err}")
            self.db.rollback()
        except Exception as err:
            logger.warning(f"Unknown error with message: {err}")
            self.db.rollback()
