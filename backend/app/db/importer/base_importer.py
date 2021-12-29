import logging

from sqlalchemy import exc
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import FlushError

from app.models import CarFuelDataCar

logger = logging.getLogger(__name__)


class BaseImporter:
    def __init__(self, db: Session):
        self.db = db
        self._int_hashes = {}

    def fallback_importer(
        self, object_collection: list, merge_on_duplicate: bool = True
    ) -> None:
        """
        Working as the general importer with a duplicate key check build in. If a duplicate exists it is removed from the
        collection. If a key exists in the database the entry is merged, if set to true.

        :param object_collection: collection of Database Models
        :param merge_on_duplicate: Set to ture to merge existing database objects.
        """
        counter = 0
        db_object_hashes: set = set()
        for i in range(len(object_collection) - 1, -1, -1):
            db_object: CarFuelDataCar = object_collection[i]
            if db_object.id not in db_object_hashes:
                db_object_hashes.add(db_object.id)
            else:
                object_collection.pop(i)
                counter += 1
                continue
            if merge_on_duplicate and object_collection[i].get_all_by_filter(
                self.db, [object_collection[i].id]
            ):
                self.db.merge(object_collection.pop(i))

        try:
            self.db.add_all(object_collection)
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
