from app.core.config import settings
from app.db.importer.carfueldata.cfd_reader import CarFuelDataReader
from app.models import CarFuelDataCar


def test_cfd_reader() -> None:
    cfd_test: CarFuelDataReader = CarFuelDataReader(
        settings.CARFUELDATA_TEST_PATH_OR_URL
    )
    cfd_test.fetch_and_process_data()
    assert len(cfd_test.objects_list) == 649
    cfd_object: CarFuelDataCar
    for cfd_object in cfd_test.objects_list:
        assert issubclass(type(cfd_object), CarFuelDataCar)
        assert len(cfd_object.__dict__) == 47
