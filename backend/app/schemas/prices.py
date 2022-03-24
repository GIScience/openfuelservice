from pydantic_sqlalchemy import sqlalchemy_to_pydantic

from app.models import EurostatCountryPrice, EurostatGeneralPrice


class GeneralPrice(sqlalchemy_to_pydantic(EurostatGeneralPrice)):  # type: ignore
    class Config:
        arbitrary_types_allowed = True
        orm_mode = True


class CountryPrice(sqlalchemy_to_pydantic(EurostatCountryPrice)):  # type: ignore
    class Config:
        arbitrary_types_allowed = True
        orm_mode = True
