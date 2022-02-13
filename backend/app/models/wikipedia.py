from typing import TYPE_CHECKING

from sqlalchemy import ARRAY, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .carfueldata import CarFuelDataAverageCategoryStatistics  # noqa: F401
    from .envirocar import EnvirocarAverageCategoryStatistics  # noqa: F401

    hybrid_property = property
else:
    from sqlalchemy.ext.hybrid import hybrid_property


class WikiCarCategory(Base):
    # CarCategoryModel
    # wikicarcategory
    id = Column(String, primary_key=True, nullable=False, index=True)

    @hybrid_property
    def category_short_eu(self) -> str:
        return self.id

    @category_short_eu.setter
    def category_short_eu(self, value: str) -> None:
        self.id = value

    category_name_de = Column(String, unique=True, nullable=False, index=True)
    category_name_en = Column(String, unique=True, nullable=False, index=True)

    category_wiki_names = Column(ARRAY(String), nullable=False)

    car_models = relationship(
        "WikiCar", backref="{}".format("{}".format("wikicarcategory")), lazy="dynamic"
    )
    wiki_car_page_texts = relationship(
        "WikiCarPageText", backref="{}".format("wikicarcategory"), lazy="dynamic"
    )

    carfueldata_av_statistics = relationship(
        "CarFuelDataAverageCategoryStatistics",
        backref="{}".format("wikicarcategory"),
        lazy="dynamic",
    )

    average_category_statistics = relationship(
        "EnvirocarAverageCategoryStatistics",
        backref="{}".format("wikicarcategory"),
        lazy="dynamic",
    )


class WikiCar(Base):
    # WikiCarModel
    # wiki_car_table
    id = Column(Integer, primary_key=True)

    @hybrid_property
    def page_id(self) -> int:
        return self.id

    @page_id.setter
    def page_id(self, value: int) -> None:
        self.id = int(value)

    wiki_name = Column(String, nullable=False, index=True)
    category_short_eu = Column(
        String, ForeignKey("{}.id".format("wikicarcategory")), nullable=True, index=True
    )
    category = relationship(WikiCarCategory, back_populates="car_models")

    brand_name = Column(String, nullable=False, index=True)
    car_name = Column(String, nullable=False, index=True)
    page_language = Column(String, nullable=True)


class WikiCarPageText(Base):
    # WikiCarPageTextModel
    # wikicar_page_texts
    id = Column(
        Integer,
        ForeignKey("{}.id".format(WikiCar.__tablename__)),
        index=True,
        primary_key=True,
    )

    @hybrid_property
    def page_id(self) -> int:
        return self.id

    @page_id.setter
    def page_id(self, value: int) -> None:
        self.id = value

    brand_name = Column(String, nullable=False, index=True)
    car_name = Column(String, nullable=False, index=True)
    page_language = Column(String, nullable=False, index=True)
    page_text = Column(String, nullable=True)
    category_short_eu = Column(
        String,
        ForeignKey("{}.id".format(WikiCarCategory.__tablename__)),
        nullable=True,
        index=True,
    )
