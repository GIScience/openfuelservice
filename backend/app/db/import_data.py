from sqlalchemy.orm import Session

from app.db import base  # noqa: F401
from app.db.importer.carfueldata.cfd_importer import CarFuelDataImporter
from app.db.importer.carfueldata.cfd_reader import CarFuelDataReader


def import_data(db: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line
    # Base.metadata.create_all(bind=engine)

    cfd_reader = CarFuelDataReader()
    cfd_reader.fetch_data()
    CarFuelDataImporter(db=db).import_cfd_reader(cfd_reader=cfd_reader)
