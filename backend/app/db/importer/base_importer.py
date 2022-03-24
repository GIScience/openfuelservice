import logging
from typing import Dict, List

from sqlalchemy import exc
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import FlushError
from tqdm import tqdm

from app.db.base_class import Base

logger = logging.getLogger(__name__)


class BaseImporter:
    def __init__(self, db: Session):
        self._db: Session = db
        self._int_hashes: Dict = {}
        self._object_collection: List = []

    def import_data(self, db_objects: List[Base]) -> None:
        for database_object in tqdm(
            db_objects,
            total=len(db_objects),
            unit=" DB Objects",
            desc=" Importing Database Objects.",
        ):
            if issubclass(type(database_object), Base):
                self._object_collection.append(database_object)
        self._fallback_importer()

    def import_data_ordered(self, db_objects_ordered: Dict[int, List[Base]]) -> None:
        for index, object_collection in db_objects_ordered.items():
            self.import_data(db_objects=object_collection)

    def _fallback_importer(self, merge_on_duplicate: bool = True) -> None:
        """
        Working as the general importer with a duplicate key check build in. If a duplicate exists it is removed from
        the collection. If a key exists in the database the entry is merged, if set to true.

        :param merge_on_duplicate: Set to ture to merge existing database objects.
        """
        # Check per object class for duplicate objects
        db_object_hashes: Dict = {}
        for i in range(len(self._object_collection) - 1, -1, -1):
            db_object: Base = self._object_collection[i]
            if str(type(db_object)) not in db_object_hashes:
                db_object_hashes[str(type(db_object))] = set()
            object_hash: str = db_object.hash_object()
            if object_hash not in db_object_hashes[str(type(db_object))]:
                db_object_hashes[str(type(db_object))].add(object_hash)
            else:
                self._object_collection.pop(i)
        try:
            self._db.add_all(self._object_collection)
            self._db.commit()
        except exc.IntegrityError as err:
            logger.warning(f"Integrity error with message: {err}")
            self._db.rollback()
            for i in range(len(self._object_collection) - 1, -1, -1):
                existing_objects: List = self._object_collection[i].get_all_by_filter(
                    self._db, [self._object_collection[i].id]
                )
                if merge_on_duplicate and len(existing_objects):
                    self._db.merge(self._object_collection.pop(i))
                elif len(existing_objects):
                    self._object_collection.pop(i)
            self._fallback_importer(merge_on_duplicate=merge_on_duplicate)
        except TypeError as err:
            logger.warning(f"Type error with message: {err}")
            self._db.rollback()
        except FlushError as err:
            logger.warning(f"Flush error with message: {err}")
            self._db.rollback()
        except Exception as err:
            logger.warning(f"Unknown error with message: {err}")
            self._db.rollback()
