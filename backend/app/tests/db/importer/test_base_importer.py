from typing import List

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.importer.base_importer import BaseImporter
from app.db.importer.carfueldata.cfd_reader import CarFuelDataReader
from app.models import CarFuelDataCar


def test_base_importer(db: Session) -> None:
    cfd_reader_test: CarFuelDataReader = CarFuelDataReader(
        settings.CARFUELDATA_TEST_PATH_OR_URL
    )
    cfd_reader_test.fetch_and_process_data()
    BaseImporter(db=db).import_data(reader_object=cfd_reader_test)
    car: CarFuelDataCar
    unique_ids: List = list(set([car.id for car in cfd_reader_test.objects_list]))
    assert len(
        CarFuelDataCar.get_all_by_filter(db=db, filter_ids=unique_ids, id_only=True)
    ) == len(unique_ids)
