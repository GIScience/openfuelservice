from typing import Any, Dict, List

from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Session

from app.db.importer.mappings import BaseMapping


@as_declarative()
class Base:
    id: Any

    __name__: str

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    @classmethod
    def get_all_by_filter(cls, db: Session, filter_ids: list) -> list:
        return cls.query().filter(cls.id.in_(filter_ids)).all()  # type: ignore

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
            elif type(value) == str and value.lower() in ["true", "yes", "no", "false"]:
                value = bool(value)
            self.__setattr__(key.name.lower(), value)
