# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa
from app.models.carfueldata import CarFuelDataAverageCategoryStatistics  # noqa
from app.models.carfueldata import CarFuelDataCar  # noqa
from app.models.eurostat import EurostatCountryPrice  # noqa
from app.models.eurostat import EurostatGeneralPrice  # noqa
from app.models.item import Item  # noqa
from app.models.user import User  # noqa
from app.models.wikipedia import WikiCar  # noqa
from app.models.wikipedia import WikiCarCategory  # noqa
from app.models.wikipedia import WikiCarPageText  # noqa
