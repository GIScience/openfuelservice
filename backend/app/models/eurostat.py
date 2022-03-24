import datetime
import logging
from typing import TYPE_CHECKING, Union

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Numeric, String

from app.db.base_class import Base

if TYPE_CHECKING:
    from .countrydata import CountryData  # noqa: F401

    hybrid_property = property
else:
    from sqlalchemy.ext.hybrid import hybrid_property
logger = logging.getLogger(__name__)


class EurostatGeneralPrice(Base):
    # EurostatGeneralPriceModel
    # general_prices
    id = Column(DateTime, index=True, nullable=False, primary_key=True, unique=True)

    @hybrid_property
    def date(self) -> Union[datetime.datetime, datetime.date]:
        return self.id

    @date.setter
    def date(self, date: datetime.datetime) -> None:
        if isinstance(date, datetime.date) or isinstance(date, datetime.datetime):
            self.id = date
        else:
            logger.debug(
                f"Couldn't varify date variable: {date} with type class: {type(date)}"
            )

    price_in_euro = Column(Integer, nullable=False, default=1)
    euro_ht = Column(Numeric, nullable=True)
    euro_ttc = Column(Numeric, nullable=True)
    euro_unit = Column(String, nullable=False)
    euro_quantity = Column(Integer, nullable=False)
    diesel_ht = Column(Numeric, nullable=True)
    diesel_ttc = Column(Numeric, nullable=True)
    diesel_unit = Column(String, nullable=False)
    diesel_quantity = Column(Integer, nullable=False)

    @hybrid_property
    def is_valid(self) -> bool:
        if any(
            value is None
            for value in [
                self.id,
                self.price_in_euro,
                self.euro_unit,
                self.euro_quantity,
                self.diesel_unit,
                self.diesel_quantity,
            ]
        ):
            return False
        return True


class EurostatCountryPrice(Base):
    # EurostatCountryPriceModel
    # country_prices
    id = Column(DateTime, index=True, primary_key=True)

    @hybrid_property
    def date(self) -> Union[datetime.date, datetime.datetime]:
        return self.id

    @date.setter
    def date(self, date: datetime.datetime) -> None:
        if isinstance(date, datetime.date) or isinstance(date, datetime.datetime):
            self.id = date
        else:
            logger.debug(
                f"Couldn't varify date variable: {date} with type class: {type(date)}"
            )

    country_alpha_2 = Column(
        String,
        ForeignKey("{}.country_alpha_2".format("countrydata")),
        index=True,
        primary_key=True,
    )

    # __table_args__ = (
    #     ForeignKeyConstraint(
    #         ['country_alpha_2'],
    #         ['countrydata.country_alpha_2'],
    #     ),
    #     PrimaryKeyConstraint(id, country_alpha_2),
    # )

    taux = Column(Float)
    price_in_euro = Column(Integer, nullable=False, default=1)
    euro_ht = Column(Numeric, nullable=True)
    euro_ttc = Column(Numeric, nullable=True)
    euro_unit = Column(String, nullable=False)
    euro_quantity = Column(Integer, nullable=False)
    diesel_ht = Column(Numeric, nullable=True)
    diesel_ttc = Column(Numeric, nullable=True)
    diesel_unit = Column(String, nullable=False)
    diesel_quantity = Column(Integer, nullable=False)

    @hybrid_property
    def is_valid(self) -> bool:
        if any(
            value is None
            for value in [
                self.date,
                self.country_alpha_2,
                self.taux,
                self.price_in_euro,
                self.euro_unit,
                self.euro_quantity,
                self.diesel_unit,
                self.diesel_quantity,
            ]
        ):
            return False
        return True
