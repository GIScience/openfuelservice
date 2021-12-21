from typing import TYPE_CHECKING

from sqlalchemy import (
    CHAR,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
)

from app.db.base_class import Base

if TYPE_CHECKING:
    from .countrydata import CountryData  # noqa: F401


class EurostatCountryPrice(Base):
    # EurostatCountryPriceModel
    # country_prices
    hash_id = Column(CHAR(length=32), primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    country_alpha_2 = Column(
        String,
        ForeignKey("{}.country_alpha_2".format("countrydata")),
        nullable=False,
        index=True,
    )
    taux = Column(Float)
    euro_price = Column(Integer, nullable=True)
    euro_ht = Column(Numeric, nullable=True)
    euro_ttc = Column(Numeric, nullable=True)
    euro_unit = Column(String, nullable=False)
    euro_quantity = Column(Integer, nullable=False)
    diesel_ht = Column(Numeric, nullable=True)
    diesel_ttc = Column(Numeric, nullable=True)
    diesel_unit = Column(String, nullable=False)
    diesel_quantity = Column(Integer, nullable=False)


class EurostatGeneralPriceModel(Base):
    # EurostatGeneralPriceModel
    # general_prices
    hash_id = Column(CHAR(length=32), primary_key=True, unique=True)
    date = Column(DateTime, nullable=False, primary_key=True, unique=True)
    euro_price = Column(Integer, nullable=True)
    euro_ht = Column(Numeric, nullable=True)
    euro_ttc = Column(Numeric, nullable=True)
    euro_unit = Column(String, nullable=False)
    euro_quantity = Column(Integer, nullable=False)
    diesel_ht = Column(Numeric, nullable=True)
    diesel_ttc = Column(Numeric, nullable=True)
    diesel_unit = Column(String, nullable=False)
    diesel_quantity = Column(Integer, nullable=False)
