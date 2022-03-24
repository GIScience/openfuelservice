import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.importer.base_importer import BaseImporter
from app.models import EurostatGeneralPrice


def test_base_importer(db: Session) -> None:
    current_datetime: datetime.datetime = datetime.datetime.now()
    eurostat_general_price = EurostatGeneralPrice()
    eurostat_general_price.price_in_euro = 0
    eurostat_general_price.date = current_datetime
    eurostat_general_price.euro_ht = Decimal(1)
    eurostat_general_price.euro_unit = "liter"
    eurostat_general_price.euro_ttc = Decimal(3)
    eurostat_general_price.euro_quantity = 4
    eurostat_general_price.diesel_ht = Decimal(5)
    eurostat_general_price.diesel_unit = "liter"
    eurostat_general_price.diesel_ttc = Decimal(7)
    eurostat_general_price.diesel_quantity = 8
    BaseImporter(db=db).import_data([eurostat_general_price])
    db_objects = (
        db.query(EurostatGeneralPrice)
        .filter(EurostatGeneralPrice.id == current_datetime)
        .all()
    )
    assert len(db_objects) == 1
    key: str
    for key, value in db_objects[0].__dict__.items():
        if key.startswith("_"):
            continue
        assert key in eurostat_general_price.__dict__.keys()
        assert value == eurostat_general_price.__dict__.get(key)
    db.delete(eurostat_general_price)
