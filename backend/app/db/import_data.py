import logging

from sqlalchemy.orm import Session

from app.db import base  # noqa: F401
from app.db.importer.base_importer import BaseImporter
from app.db.importer.envirocar.envirocar_reader import EnvirocarReader

logger = logging.getLogger(__name__)


def import_data(db: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line
    # Base.metadata.create_all(bind=engine)

    # cfd_reader = CarFuelDataReader(settings.CARFUELDATA_PATH_OR_URL)
    # cfd_reader.fetch_and_process_data()
    # BaseImporter(db=db).import_data(db_objects=cfd_reader.objects_list)

    envirocar_reader: EnvirocarReader = EnvirocarReader(
        file_or_url=None, envirocar_base_url="https://test.com", threads=None
    )
    envirocar_reader.fetch_and_process_data()
    for index, object_collection in envirocar_reader.objects_ordered.items():
        BaseImporter(db=db).import_data(db_objects=object_collection)
