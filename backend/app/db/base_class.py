from typing import Any

from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Session


@as_declarative()
class Base:
    id: Any
    #  hash_id = Column(CHAR(length=32), primary_key=True)

    __name__: str

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    @classmethod
    def get_all_by_filter(cls, db: Session, filter_ids: list) -> list:
        return cls.query().filter(cls.id.in_(filter_ids)).all()  # type: ignore
