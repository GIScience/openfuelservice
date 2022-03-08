import datetime
import hashlib
from typing import Any, Dict, List, Union

import numpy
from geoalchemy2 import WKBElement
from psycopg2.extensions import AsIs, register_adapter
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session, validates

from app.db.importer.mappings import BaseMapping
from app.misc import json_decoders


@as_declarative()
class Base:
    id: Any

    __name__: str

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    @classmethod
    def get_all_by_filter(
        cls, db: Session, filter_ids: list, id_only: bool = False
    ) -> list:
        if id_only:
            return db.query(cls.id).filter(cls.id.in_(filter_ids)).distinct().all()
        else:
            return db.query(cls).filter(cls.id.in_(filter_ids)).all()

    def set_data(self, data: List, headers: Dict) -> None:
        value: Any
        key: BaseMapping
        for key, header_index in headers.items():
            value = data[header_index]
            if value is None or str(value).lower().strip() == "n/a" or key is None:
                value = None
            elif type(value) == str and not len(value):
                value = None
            elif type(value) == str and "." in value and value.isdigit():
                value = float(value)
            elif type(value) == str and value.isdigit():
                value = int(value)
            elif type(value) == str and value.lower() in ["true", "false"]:
                value = bool(value)
            self.__setattr__(key.name.lower(), value)

    def hash_object(self) -> str:
        hash_string: str = ""

        primary_keys = [key.name for key in inspect(self.__class__).primary_key]

        key: str
        for key in primary_keys:
            if key.startswith("_") or key not in self.__dict__.keys():
                continue
            value: Any = self.__dict__.get(key)
            if isinstance(value, datetime.datetime) or isinstance(value, datetime.date):
                value = value.strftime("%Y%m%d")
            hash_string = f"{hash_string}{str(value).strip()}"
        return hashlib.md5(hash_string.strip(" ").encode("utf-8")).hexdigest()

    @validates("geom")
    def validate_geom(self, _: str, geom: Any) -> Union[WKBElement, None]:
        return json_decoders.json_to_wkb_element(geom)


def addapt_numpy_float64(numpy_float64: Any) -> AsIs:
    return AsIs(numpy_float64)


def addapt_numpy_float32(numpy_float32: Any) -> AsIs:
    return AsIs(numpy_float32)


def addapt_numpy_int64(numpy_int64: Any) -> AsIs:
    return AsIs(numpy_int64)


register_adapter(numpy.float64, addapt_numpy_float64)
register_adapter(numpy.float32, addapt_numpy_float32)
register_adapter(numpy.int64, addapt_numpy_int64)
