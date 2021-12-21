from typing import TYPE_CHECKING

from sqlalchemy import CHAR, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .carfueldata import CarFuelDataAverageCategoryStatistics  # noqa: F401


class WikiCar(Base):
    # WikiCarModel
    # wiki_car_table
    hash_id = Column(CHAR(length=32), primary_key=True, index=True)
    wiki_name = Column(String, nullable=False, index=True)
    category_short_eu = Column(
        String,
        ForeignKey("{}.category_short_eu".format("wikicarcategory")),
        nullable=True,
        index=True,
    )
    brand_name = Column(String, nullable=False, index=True)
    car_name = Column(String, nullable=False, index=True)
    page_id = Column(Integer, nullable=True)
    page_language = Column(String, nullable=True)


class WikiCarCategory(Base):
    # CarCategoryModel
    # wikicarcategory
    category_short_eu = Column(String, primary_key=True, nullable=False, index=True)
    category_name_de = Column(String, unique=True, nullable=False, index=True)
    category_name_en = Column(String, unique=True, nullable=False, index=True)

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


class WikiCarPageText(Base):
    # WikiCarPageTextModel
    # wikicar_page_texts
    hash_id = Column(CHAR(length=32), primary_key=True, index=True)
    wiki_name = Column(String, nullable=False, index=True)
    brand_name = Column(String, nullable=False, index=True)
    car_name = Column(String, nullable=False, index=True)
    page_language = Column(String, nullable=False, index=True)
    page_text = Column(String, nullable=True)
    category_short_eu = Column(
        String,
        ForeignKey("{}.category_short_eu".format(WikiCarCategory.__tablename__)),
        nullable=True,
        index=True,
    )
