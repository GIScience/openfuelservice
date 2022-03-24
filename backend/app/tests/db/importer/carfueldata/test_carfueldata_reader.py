import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.importer.carfueldata.carfueldata_reader import CarFuelDataReader
from app.models import CarFuelDataCar


@pytest.mark.asyncio
async def test_carfueldata_reader(db: Session) -> None:
    cfd_test: CarFuelDataReader = CarFuelDataReader(
        db=db, file_to_read=settings.CARFUELDATA_TEST_PATH_OR_URL
    )
    await cfd_test.fetch_process_and_import_data(import_data=False)
    assert len(cfd_test.objects_list) == 649
    cfd_object: CarFuelDataCar
    for cfd_object in cfd_test.objects_list:
        assert issubclass(type(cfd_object), CarFuelDataCar)
        assert len(cfd_object.__dict__) == 46
        assert not cfd_object.id
