from typing import List

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.importer.base_importer import BaseImporter
from app.db.importer.carfueldata.carfueldata_reader import CarFuelDataReader
from app.models import CarFuelDataCar


def test_cfd_importer(db: Session) -> None:
    cfd_reader_test: CarFuelDataReader = CarFuelDataReader(
        settings.CARFUELDATA_TEST_PATH_OR_URL
    )
    cfd_reader_test.fetch_and_process_data()
    BaseImporter(db=db).import_data(db_objects=cfd_reader_test.objects_list)
    car: CarFuelDataCar
    unique_ids: List = list(
        set([car.id for car in cfd_reader_test.objects_list if car.id is not None])
    )
    unique_ids_db = CarFuelDataCar.get_all_by_filter(
        db=db, filter_ids=unique_ids, id_only=True
    )
    unique_ids_db = [x[0] for x in unique_ids_db]

    assert len(unique_ids_db) == len(unique_ids)
    assert all(object_id in unique_ids_db for object_id in unique_ids)

    assert len(unique_ids_db) == 602

    cfd_car: CarFuelDataCar
    for cfd_car in cfd_reader_test.objects_list:
        assert cfd_car.id in unique_ids_db if cfd_car.id is not None else True

    CarFuelDataCar.__table__.delete().where(CarFuelDataCar.id.in_([unique_ids_db]))
