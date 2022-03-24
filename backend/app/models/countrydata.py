from typing import TYPE_CHECKING

from geoalchemy2 import Geometry
from sqlalchemy import VARCHAR, Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .eurostat import EurostatCountryPrice  # noqa: F401


class CountryData(Base):
    # CountryDataModel
    # countries_table
    id = Column(String, primary_key=True, index=True)
    country_name = Column(String, primary_key=True, index=True)
    country_alpha_2 = Column(String, unique=True, nullable=True, index=True)
    country_alpha_3 = Column(VARCHAR, unique=True, index=True, nullable=True)
    country_numeric = Column(Integer, index=True, nullable=True)
    country_currency_code = Column(String, index=True, nullable=True)
    country_currency_name = Column(String, index=True, nullable=True)
    geom = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=True))
    country_prices = relationship("EurostatCountryPrice", lazy="dynamic")
