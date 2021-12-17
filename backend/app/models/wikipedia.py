import logging

from sqlalchemy import CHAR, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

logger = logging.getLogger(__package__)


class WikiCar(Base):
    # WikiCarModel
    # wiki_car_table
    hash_id = Column(CHAR(length=32), primary_key=True, unique=True)
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

    def __repr__(self):
        return "<car wiki name {}>".format(self.wiki_name)

    def __hash__(self):
        return hash(self.wiki_name)


class WikiCarCategory(Base):
    # CarCategoryModel
    # wikicarcategory
    category_short_eu = Column(
        String, primary_key=True, unique=True, nullable=False, index=True
    )
    category_name_de = Column(String, unique=True, nullable=False, index=True)
    category_name_en = Column(String, unique=True, nullable=False, index=True)

    car_models = relationship(
        "WikiCar", backref="{}".format("{}".format("wikicarcategory")), lazy="dynamic"
    )
    wiki_car_page_texts = relationship(
        "WikiCarPageText", backref="{}".format("wikicarcategory"), lazy="dynamic"
    )
    # carfueldata_av_statistics = relationship('CarFuelDataAverageCategoryStatisticsModel',
    #                                          backref='{}'.format(
    #                                              wikicarcategory),
    #                                          lazy='dynamic')
    # average_category_statistics = relationship('EnvirocarAverageCategoryStatisticsModel', backref='{}'.format(
    #     wikicarcategory),
    #                                            lazy='dynamic')

    def __repr__(self):
        return "<category wiki {}>".format(self.category_short_eu)

    def __hash__(self):
        return hash(self.category_short_eu)


class WikiCarPageText(Base):
    # WikiCarPageTextModel
    # wikicar_page_texts
    id = Column(Integer, primary_key=True, index=True, unique=True)
    hash_id = Column(CHAR(length=32), primary_key=True, unique=True)
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
