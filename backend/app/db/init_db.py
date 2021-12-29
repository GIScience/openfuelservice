from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import settings
from app.db import base  # noqa: F401
from app.db.importer.carfueldata.cfd_importer import CarFuelDataImporter
from app.db.importer.carfueldata.cfd_reader import CarFuelDataReader


def init_db(db: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line
    # Base.metadata.create_all(bind=engine)

    user = crud.user.get_by_email(db, email=settings.FIRST_SUPERUSER)
    if not user:
        user_in = schemas.UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.user.create(db, obj_in=user_in)  # noqa: F841

    # Get CFD data
    cfd_reader = CarFuelDataReader()
    cfd_reader.fetch_data()
    CarFuelDataImporter(db=db).import_cfd_reader(cfd_reader=cfd_reader)
