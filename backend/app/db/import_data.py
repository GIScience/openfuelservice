from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import base  # noqa: F401
from app.db.importer.base_importer import BaseImporter
from app.db.importer.carfueldata.cfd_reader import CarFuelDataReader


def import_data(db: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line
    # Base.metadata.create_all(bind=engine)

    cfd_reader = CarFuelDataReader(settings.CARFUELDATA_PATH_OR_URL)
    cfd_reader.fetch_and_process_data()
    BaseImporter(db=db).import_data(db_objects=cfd_reader.objects_list)
